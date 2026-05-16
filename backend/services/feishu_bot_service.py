"""飞书机器人业务逻辑服务"""

import logging
from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.api.v1.feishu_binding import bind_feishu_by_code
from backend.clients.feishu_client import feishu_client
from backend.models.action_item import ActionItem
from backend.models.raw_info import RawInfo
from backend.models.user import User
from backend.services.command_service import BINDING_CODE_LENGTH, command_service
from backend.services.digest_service import create_raw_info, process_digest_sync

logger = logging.getLogger(__name__)


class FeishuBotService:
    """飞书机器人业务逻辑服务"""

    async def handle_message(
        self, db: AsyncSession, open_id: str, message_id: str, text: str, chat_id: str | None = None
    ) -> None:
        """
        处理飞书消息

        Args:
            db: 数据库会话
            open_id: 飞书用户 open_id
            message_id: 消息 ID
            text: 消息文本
            chat_id: 群聊 ID（群聊时传入）
        """
        try:
            # 2. 解析命令
            command_type, params = command_service.parse_command(text)

            # 3. 路由到不同处理方法
            if command_type == "bind":
                # 绑定命令特殊处理，不需要先获取用户
                reply_text = await self.handle_binding(db, open_id, params.get("binding_code", ""))
            else:
                # 其他命令需要先获取或创建用户
                user = await self.get_or_create_user_by_feishu(db, open_id)
                if not user:
                    logger.error(f"Failed to get or create user for open_id: {open_id}")
                    await feishu_client.reply_message(message_id, "text", {"text": "处理用户信息时出错，请稍后重试。"})
                    return

                if command_type == "query_todo":
                    reply_text = await self.query_todos(db, user.id)
                elif command_type == "help":
                    reply_text = self.get_help_text()
                elif command_type == "process":
                    reply_text = await self.process_content(db, user.id, params.get("content", ""))
                else:
                    reply_text = "抱歉，我没有理解您的意思。发送'帮助'查看使用说明。"

            # 4. 回复消息
            await feishu_client.reply_message(message_id, "text", {"text": reply_text})

        except Exception as e:
            logger.error(f"Error handling message: {e}", exc_info=True)
            await feishu_client.reply_message(message_id, "text", {"text": "处理消息时出错，请稍后重试。"})

    async def handle_binding(self, db: AsyncSession, open_id: str, binding_code: str) -> str:
        """处理飞书账号绑定"""
        try:
            result = await bind_feishu_by_code(db, binding_code.upper(), open_id)

            if result["success"]:
                return "✅ 绑定成功！\n\n您的飞书账号已成功关联到 Info-Butler 账号。\n现在可以正常使用所有功能了。"
            else:
                return f"❌ {result['message']}\n\n请检查绑定码是否正确，或重新生成绑定码。"

        except Exception as e:
            logger.error(f"Error in binding: {e}", exc_info=True)
            return "绑定过程中出错，请稍后重试。"

    async def process_content(self, db: AsyncSession, user_id: int, text: str) -> str:
        """
        处理内容，生成摘要和待办事项
        """
        try:
            # 创建原始信息记录
            source_type = "url" if text.startswith("http") else "text"
            raw_info = await create_raw_info(
                db=db,
                source_type=source_type,
                content=text,
                user_id=user_id,
                title="飞书消息",
            )

            # 处理内容（跳过飞书通知，由下方 reply_message 统一回复）
            await process_digest_sync(db, raw_info, generate_actions=True, generate_tags=True, skip_feishu_notification=True)

            # 重新查询以加载关联数据
            result = await db.execute(
                select(RawInfo)
                .where(RawInfo.id == raw_info.id)
                .options(selectinload(RawInfo.tags), selectinload(RawInfo.action_items))
            )
            raw_info = result.scalar_one_or_none()

            if not raw_info or raw_info.status != "done":
                error_msg = raw_info.error_msg if raw_info else "未找到记录"
                return f"处理失败: {error_msg}"

            # 格式化回复
            lines = ["✅ 信息处理完成\n"]

            if raw_info.summary:
                lines.append(f"📝 **摘要**\n{raw_info.summary}\n")

            if raw_info.tags:
                tag_names = [t.name for t in raw_info.tags]
                tag_str = " ".join(f"#{t}" for t in tag_names)
                lines.append(f"🏷️ **标签**: {tag_str}\n")

            if raw_info.action_items:
                lines.append("📋 **行动项**:")
                for i, item in enumerate(raw_info.action_items[:5], 1):
                    priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                        item.priority, "⚪"
                    )
                    due_text = ""
                    if item.due_datetime:
                        due_text = f" 📍{item.due_datetime.strftime('%m/%d %H:%M')}提醒"
                    elif item.due_date:
                        due_text = f" 📍{item.due_date.strftime('%m/%d')}到期"
                    lines.append(f"{i}. {priority_icon} {item.content}{due_text}")
            else:
                lines.append("📋 未识别出行动项")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error processing content: {e}", exc_info=True)
            return "处理内容时出错，请稍后重试。"

    async def query_todos(self, db: AsyncSession, user_id: int) -> str:
        """
        查询待办事项，按截止时间排序

        Args:
            db: 数据库会话
            user_id: 用户 ID

        Returns:
            格式化的待办列表
        """
        try:
            # 查询待办事项（pending 状态），按截止时间排序
            result = await db.execute(
                select(ActionItem)
                .where(ActionItem.user_id == user_id, ActionItem.status == "pending")
                .order_by(ActionItem.due_date.asc(), ActionItem.priority.desc())
                .limit(10)
            )
            action_items = result.scalars().all()

            if not action_items:
                return "🎉 当前没有待办事项！"

            lines = ["📋 **待办事项列表**\n"]

            now = datetime.now().date()
            for i, item in enumerate(action_items, 1):
                priority_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(item.priority, "⚪")

                due_text = ""
                if item.due_date:
                    days_diff = (item.due_date - now).days
                    if days_diff < 0:
                        due_text = f" ⚠️已逾期{abs(days_diff)}天"
                    elif days_diff == 0:
                        due_text = " 📍今天到期"
                    elif days_diff == 1:
                        due_text = " 📍明天到期"
                    elif days_diff <= 3:
                        due_text = f" 📍{days_diff}天后到期"

                lines.append(f"{i}. {priority_icon} {item.content}{due_text}")

            return "\n".join(lines)

        except Exception as e:
            logger.error(f"Error querying todos: {e}", exc_info=True)
            return "查询待办事项时出错，请稍后重试。"

    async def get_or_create_user_by_feishu(self, db: AsyncSession, open_id: str) -> User | None:
        """根据飞书 open_id 获取或创建用户"""
        try:
            # 1. 查找已绑定的用户
            result = await db.execute(select(User).where(User.feishu_open_id == open_id))
            user = result.scalar_one_or_none()

            if user:
                logger.info(f"Found existing user with feishu_open_id: {open_id[:6]}...")
                return user

            # 2. 获取飞书用户信息
            user_info = await feishu_client.get_user_info(open_id)
            feishu_email = user_info.get("email") if user_info else None
            feishu_name = user_info.get("name", f"feishu_{open_id[:10]}") if user_info else f"feishu_{open_id[:10]}"

            # 3. 尝试通过邮箱关联现有用户
            if feishu_email:
                result = await db.execute(select(User).where(User.email == feishu_email))
                existing_user = result.scalar_one_or_none()

                if existing_user and not existing_user.feishu_open_id:
                    await db.execute(
                        update(User).where(User.id == existing_user.id).values(feishu_open_id=open_id)
                    )
                    await db.commit()
                    await db.refresh(existing_user)
                    logger.info(f"Linked feishu account to existing user: {existing_user.email[:3]}***")
                    return existing_user

            # 4. 创建新用户（仅限已绑定邮箱的飞书用户）
            if not feishu_email:
                logger.warning(f"Cannot auto-create user for open_id: {open_id[:6]}... - no email available")
                return None

            email = feishu_email
            username = feishu_name

            result = await db.execute(select(User).where(User.username == username))
            if result.scalar_one_or_none():
                username = f"{username}_{open_id[:6]}"

            result = await db.execute(select(User).where(User.email == email))
            if result.scalar_one_or_none():
                logger.warning(f"Email already exists, cannot auto-create for open_id: {open_id[:6]}...")
                return None

            from secrets import token_urlsafe

            from backend.core.security import get_password_hash

            random_password = token_urlsafe(32)
            hashed_password = get_password_hash(random_password)

            user = User(
                username=username,
                email=email,
                hashed_password=hashed_password,
                feishu_open_id=open_id,
                is_active=True,
            )

            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"Created new user for feishu open_id: {open_id[:6]}...")
            return user

        except Exception as e:
            logger.error(f"Error getting or creating user: {e}", exc_info=True)
            await db.rollback()
            return None

    def get_help_text(self) -> str:
        """获取帮助文本"""
        return (
            "🤖 **Info-Butler 机器人使用说明**\n\n"
            "## 📝 添加待办事项\n"
            "直接发送任务描述，我会自动提取并创建待办事项：\n"
            "• `明天上午9点开会`\n"
            "• `下周五之前完成报告`\n"
            "• `帮定一个明天九点的闹钟`\n\n"
            "## 📋 查询待办事项\n"
            "发送以下任一关键词查看待办列表：\n"
            "• `待办` / `todo` / `任务` / `清单`\n"
            "• `我有什么待办` / `查看待办`\n\n"
            "## 🔗 绑定账号\n"
            "如果您已有网页版账号，可以绑定飞书：\n"
            "1. 在网页端【个人设置】获取绑定码\n"
            "2. 在这里发送：`绑定 A1B2C3`（替换为您的绑定码）\n\n"
            "## 💡 智能功能\n"
            "• 发送文本或链接 → 自动生成摘要和待办\n"
            "• 待办事项到期前 → 主动发送提醒\n"
            "• 按截止时间排序 → 重要事项优先展示\n\n"
            "## 🆘 其他功能\n"
            "• 发送链接 → 自动抓取内容并生成摘要\n"
            "• 发送`帮助` → 查看此帮助信息"
        )


feishu_bot_service = FeishuBotService()
