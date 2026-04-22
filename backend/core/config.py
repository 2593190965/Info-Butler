from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "Info-Butler"
    app_env: str = "development"
    debug: bool = True
    api_key: str = "dev-api-key-2026"
    jwt_secret: str = "info-butler-jwt-secret-key-change-in-production-2026"

    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_user: str = "root"
    mysql_password: str = "root"
    mysql_database: str = "info_butler"

    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_password: str = ""
    redis_db: int = 0

    dify_api_url: str = "https://api.dify.ai/v1"
    dify_api_key: str = ""
    dify_workflow_id: str = ""

    feishu_webhook_url: str = ""

    @property
    def mysql_dsn(self) -> str:
        return (
            f"mysql+aiomysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}"
            "?charset=utf8mb4"
        )

    @property
    def redis_url(self) -> str:
        pw_part = f":{self.redis_password}@" if self.redis_password else "@"
        return f"redis://{pw_part}{self.redis_host}:{self.redis_port}/{self.redis_db}"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
