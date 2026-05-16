import logging
from datetime import date, datetime, timedelta

from sqlalchemy import select, update

logger = logging.getLogger(__name__)


async def process_digest(ctx, task_id: str, generate_actions: bool = True, generate_tags: bool = True):
    from backend.core.database import async_session
    from backend.models.raw_info import RawInfo
    from backend.services.digest_service import get_digest_by_task_id, process_digest_sync

    logger.info(f"Processing digest task: {task_id}, actions={generate_actions}, tags={generate_tags}")

    async with async_session() as db:
        raw_info = await get_digest_by_task_id(db, task_id)
        if not raw_info:
            logger.error(f"Task {task_id} not found")
            return {"status": "error", "reason": "not_found"}

        if raw_info.status == "done":
            logger.info(f"Task {task_id} already done, skipping")
            return {"status": "skipped", "reason": "already_done"}

        try:
            await process_digest_sync(
                db, raw_info, generate_actions=generate_actions, generate_tags=generate_tags
            )
            logger.info(f"Task {task_id} processed successfully")
            return {"status": "done", "info_id": raw_info.id}
        except Exception as e:
            logger.exception(f"Task {task_id} failed: {e}")
            try:
                await db.rollback()
                await db.execute(
                    update(RawInfo)
                    .where(RawInfo.task_id == task_id)
                    .values(status="failed", error_msg=f"Worker error: {e}")
                )
                await db.commit()
            except Exception as commit_err:
                logger.error(f"Failed to update status for task {task_id}: {commit_err}")
            raise


async def send_due_reminders(ctx=None):
    """
    发送即将到期的待办提醒

    每天早上执行，提醒用户即将到期的待办事项
    """
    from backend.clients.feishu_client import feishu_client
    from backend.core.config import settings
    from backend.core.database import async_session
    from backend.models.action_item import ActionItem
    from backend.models.user import User

    logger.info("Running send_due_reminders task")

    # 计算提醒范围（提前 N 天）
    advance_days = settings.feishu_reminder_advance_days
    reminder_date = date.today() + timedelta(days=advance_days)

    async with async_session() as db:
        try:
            # 查询即将到期的待办事项（按用户分组）
            result = await db.execute(
                select(ActionItem, User)
                .join(User, ActionItem.user_id == User.id)
                .where(
                    ActionItem.status == "pending",
                    ActionItem.due_date == reminder_date,
                    User.feishu_open_id.isnot(None),
                )
                .order_by(User.id)
            )

            reminders = result.all()

            if not reminders:
                logger.info("No due reminders to send")
                return {"sent": 0}

            sent_count = 0
            for action_item, user in reminders:
                try:
                    # 发送提醒消息
                    message = (
                        f"⏰ **待办提醒**\n\n"
                        f"您有一个待办事项将在 {advance_days} 天后到期：\n\n"
                        f"📋 {action_item.content}\n\n"
                        f"截止日期：{action_item.due_date}\n"
                        f"请及时处理！"
                    )

                    success = await feishu_client.send_message(
                        open_id=user.feishu_open_id,
                        msg_type="text",
                        content={"text": message},
                    )

                    if success:
                        sent_count += 1
                        logger.info(f"Sent reminder to user {user.id} for action {action_item.id}")
                    else:
                        logger.warning(f"Failed to send reminder to user {user.id}")

                except Exception as e:
                    logger.error(f"Error sending reminder: {e}", exc_info=True)

            logger.info(f"Sent {sent_count} due reminders")
            return {"sent": sent_count}

        except Exception as e:
            logger.error(f"Error in send_due_reminders: {e}", exc_info=True)
            return {"sent": 0, "error": str(e)}


async def send_overdue_reminders(ctx=None):
    """
    发送逾期待办提醒

    每天下午执行，提醒用户已逾期的待办事项
    """
    from backend.clients.feishu_client import feishu_client
    from backend.core.database import async_session
    from backend.models.action_item import ActionItem
    from backend.models.user import User

    logger.info("Running send_overdue_reminders task")

    today = date.today()

    async with async_session() as db:
        try:
            # 查询已逾期的待办事项
            result = await db.execute(
                select(ActionItem, User)
                .join(User, ActionItem.user_id == User.id)
                .where(
                    ActionItem.status == "pending",
                    ActionItem.due_date < today,
                    User.feishu_open_id.isnot(None),
                )
                .order_by(ActionItem.due_date.asc())
            )

            reminders = result.all()

            if not reminders:
                logger.info("No overdue reminders to send")
                return {"sent": 0}

            sent_count = 0
            for action_item, user in reminders:
                try:
                    days_overdue = (today - action_item.due_date).days

                    message = (
                        f"⚠️ **逾期待办提醒**\n\n"
                        f"您有一个待办事项已逾期 {days_overdue} 天：\n\n"
                        f"📋 {action_item.content}\n\n"
                        f"截止日期：{action_item.due_date}\n"
                        f"请尽快处理！"
                    )

                    success = await feishu_client.send_message(
                        open_id=user.feishu_open_id,
                        msg_type="text",
                        content={"text": message},
                    )

                    if success:
                        sent_count += 1
                        logger.info(f"Sent overdue reminder to user {user.id} for action {action_item.id}")
                    else:
                        logger.warning(f"Failed to send overdue reminder to user {user.id}")

                except Exception as e:
                    logger.error(f"Error sending overdue reminder: {e}", exc_info=True)

            logger.info(f"Sent {sent_count} overdue reminders")
            return {"sent": sent_count}

        except Exception as e:
            logger.error(f"Error in send_overdue_reminders: {e}", exc_info=True)
            return {"sent": 0, "error": str(e)}


async def send_scheduled_reminders(ctx=None):
    """
    发送精确时间的待办提醒

    每分钟检查一次，找到当前已到提醒时间的待办事项并发送通知
    """
    from backend.clients.feishu_client import feishu_client
    from backend.core.database import async_session
    from backend.models.action_item import ActionItem
    from backend.models.user import User

    now = datetime.now()

    async with async_session() as db:
        try:
            result = await db.execute(
                select(ActionItem, User)
                .join(User, ActionItem.user_id == User.id)
                .where(
                    ActionItem.status == "pending",
                    ActionItem.due_datetime.isnot(None),
                    ActionItem.reminder_sent == False,  # noqa: E712
                    ActionItem.due_datetime <= now,
                    User.feishu_open_id.isnot(None),
                )
            )

            reminders = result.all()

            if not reminders:
                return {"sent": 0}

            sent_count = 0
            for action_item, user in reminders:
                try:
                    time_str = action_item.due_datetime.strftime("%m月%d日 %H:%M")
                    message = (
                        f"⏰ **待办提醒**\n\n"
                        f"📋 {action_item.content}\n\n"
                        f"时间：{time_str}\n"
                        f"请及时处理！"
                    )

                    success = await feishu_client.send_message(
                        open_id=user.feishu_open_id,
                        msg_type="text",
                        content={"text": message},
                    )

                    if success:
                        action_item.reminder_sent = True
                        sent_count += 1

                except Exception as e:
                    logger.error(f"Error sending scheduled reminder: {e}", exc_info=True)

            await db.commit()
            if sent_count > 0:
                logger.info(f"Sent {sent_count} scheduled reminders")
            return {"sent": sent_count}

        except Exception as e:
            logger.error(f"Error in send_scheduled_reminders: {e}", exc_info=True)
            return {"sent": 0, "error": str(e)}
