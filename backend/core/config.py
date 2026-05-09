from urllib.parse import quote

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Info-Butler"
    app_env: str = "development"
    debug: bool = True
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    api_key: str = "dev-api-key-2026"
    api_key_user_id: int = 1
    jwt_secret: str = "info-butler-jwt-secret-key-change-in-production-2026"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_database: str = "info_butler"
    mysql_test_database: str = "info_butler_test"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0
    redis_test_db: int = 15

    dify_api_url: str = "https://api.dify.ai/v1"
    dify_api_key: str = ""
    dify_workflow_id: str = ""

    feishu_webhook_url: str = ""

    rate_limit_requests: int = 100
    rate_limit_window: int = 60

    allowed_origins: str = "*"

    def model_post_init(self, __context) -> None:
        if self.app_env == "production" and self.jwt_secret == "info-butler-jwt-secret-key-change-in-production-2026":
            raise ValueError("JWT_SECRET must be changed from default value in production!")

    @property
    def allowed_origins_list(self) -> list[str]:
        if self.allowed_origins == "*":
            return ["*"]
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{quote(self.mysql_password, safe='')}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        pw_part = f":{quote(self.redis_password, safe='')}@" if self.redis_password else "@"
        return f"redis://{pw_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
