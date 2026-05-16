#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""飞书机器人配置诊断工具"""

import os
import sys
from pathlib import Path

# 设置控制台编码
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import settings


def check_feishu_config():
    """检查飞书配置"""
    print("=" * 60)
    print("飞书机器人配置诊断")
    print("=" * 60)
    print()

    issues = []
    warnings = []

    # 检查必需配置
    print("【必需配置】")
    if not settings.feishu_app_id:
        issues.append("❌ FEISHU_APP_ID 未配置")
        print("  ❌ FEISHU_APP_ID: 未配置")
    else:
        print(f"  ✅ FEISHU_APP_ID: {settings.feishu_app_id[:10]}...")

    if not settings.feishu_app_secret:
        issues.append("❌ FEISHU_APP_SECRET 未配置")
        print("  ❌ FEISHU_APP_SECRET: 未配置")
    else:
        print(f"  ✅ FEISHU_APP_SECRET: {'*' * 20}")

    print()

    # 检查可选配置
    print("【可选配置】")
    if not settings.feishu_webhook_url:
        warnings.append("⚠️  FEISHU_WEBHOOK_URL 未配置（主动推送功能不可用）")
        print("  ⚠️  FEISHU_WEBHOOK_URL: 未配置")
    else:
        print(f"  ✅ FEISHU_WEBHOOK_URL: {settings.feishu_webhook_url[:50]}...")

    if not settings.feishu_encrypt_key:
        warnings.append("⚠️  FEISHU_ENCRYPT_KEY 未配置（回调请求不会验证加密）")
        print("  ⚠️  FEISHU_ENCRYPT_KEY: 未配置")
    else:
        print("  ✅ FEISHU_ENCRYPT_KEY: 已配置")

    if not settings.feishu_verification_token:
        warnings.append("⚠️  FEISHU_VERIFICATION_TOKEN 未配置（回调请求不会验证令牌）")
        print("  ⚠️  FEISHU_VERIFICATION_TOKEN: 未配置")
    else:
        print("  ✅ FEISHU_VERIFICATION_TOKEN: 已配置")

    print(f"  ✅ FEISHU_REMINDER_ADVANCE_DAYS: {settings.feishu_reminder_advance_days} 天")
    print()

    # 检查配置文件
    print("【配置文件】")
    env_file = project_root / ".env"
    if env_file.exists():
        print(f"  ✅ .env 文件存在: {env_file}")
    else:
        issues.append("❌ .env 文件不存在")
        print(f"  ❌ .env 文件不存在")

    env_example = project_root / ".env.example"
    if env_example.exists():
        print(f"  ✅ .env.example 文件存在")
    else:
        print(f"  ⚠️  .env.example 文件不存在")

    print()

    # 检查文档
    print("【帮助文档】")
    docs = [
        ("FEISHU_SETUP_GUIDE.md", "飞书配置指南"),
        ("FEISHU_BOT_USAGE.md", "机器人使用说明"),
        ("FEISHU_ACCOUNT_BINDING.md", "账号关联说明"),
    ]

    for doc_file, doc_name in docs:
        doc_path = project_root / doc_file
        if doc_path.exists():
            print(f"  ✅ {doc_name}: {doc_file}")
        else:
            print(f"  ⚠️  {doc_name}: {doc_file} 不存在")

    print()

    # 输出诊断结果
    print("=" * 60)
    print("诊断结果")
    print("=" * 60)
    print()

    if issues:
        print("❌ 发现问题：")
        for issue in issues:
            print(f"  {issue}")
        print()

    if warnings:
        print("⚠️  警告：")
        for warning in warnings:
            print(f"  {warning}")
        print()

    if not issues:
        print("✅ 必需配置完整，机器人功能可用！")
        print()
        print("下一步：")
        print("  1. 重启应用：stop.bat → start.bat")
        print("  2. 在飞书中@机器人发送: 帮助")
        print("  3. 查看 FEISHU_BOT_USAGE.md 了解更多用法")
    else:
        print("❌ 配置不完整，请按照以下步骤操作：")
        print()
        print("  步骤 1: 访问 https://open.feishu.cn/app 创建应用")
        print("  步骤 2: 获取 App ID 和 App Secret")
        print("  步骤 3: 开通权限: im:message, im:message:send_as_bot")
        print("  步骤 4: 配置事件订阅 URL")
        print("  步骤 5: 将配置填入 .env 文件")
        print()
        print("详细步骤请查看: FEISHU_SETUP_GUIDE.md")

    print()
    print("=" * 60)

    return len(issues) == 0


if __name__ == "__main__":
    success = check_feishu_config()
    sys.exit(0 if success else 1)
