"""命令解析服务"""

BINDING_CODE_LENGTH = 16  # matches secrets.token_hex(8) in feishu_binding.py


class CommandService:
    """飞书机器人命令解析服务"""

    TODO_QUERY_KEYWORDS = [
        "待办",
        "todo",
        "任务",
        "清单",
        "待办事项",
        "todolist",
        "有什么待办",
        "我的待办",
        "查看待办",
        "待办列表",
    ]

    HELP_KEYWORDS = ["帮助", "help", "？", "?", "使用说明", "怎么用"]

    BINDING_PATTERN = "绑定"

    def parse_command(self, text: str) -> tuple[str, dict]:
        """解析命令类型，返回 (command_type, params)"""
        text_lower = text.strip().lower()

        if text_lower.startswith(self.BINDING_PATTERN):
            parts = text_lower.split()
            if len(parts) == 2 and len(parts[1]) == BINDING_CODE_LENGTH:
                return "bind", {"binding_code": parts[1].upper()}

        if self.is_todo_query(text_lower):
            return "query_todo", {}

        if self.is_help_command(text_lower):
            return "help", {}

        if text_lower:
            return "process", {"content": text_lower}

        return "unknown", {}

    def is_todo_query(self, text: str) -> bool:
        """检测是否为待办查询"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.TODO_QUERY_KEYWORDS)

    def is_help_command(self, text: str) -> bool:
        """检测是否为帮助命令"""
        text_lower = text.lower().strip()
        return text_lower in self.HELP_KEYWORDS or any(keyword in text_lower for keyword in self.HELP_KEYWORDS)


command_service = CommandService()
