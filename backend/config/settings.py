import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, model_validator
from pydantic.fields import Field, FieldInfo
from pydantic_settings import (
    BaseSettings,
    DotEnvSettingsSource,
    EnvSettingsSource,
    InitSettingsSource,
    PydanticBaseSettingsSource,
    SecretsSettingsSource,
    SettingsConfigDict,
)


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """
    YAML 配置文件加载源
    """

    def get_field_value(
        self, _field: FieldInfo, field_name: str
    ) -> tuple[Any, str, bool]:
        # 此方法在重写 __call__ 时不直接使用, 但为了满足接口定义保留
        return None, field_name, False

    def __call__(self) -> dict[str, Any]:
        # 默认从当前目录读取 config.yaml, 或通过环境变量 CONFIG_FILE 指定
        config_file = os.getenv("CONFIG_FILE", "config.yaml")
        path = Path(config_file)

        if not path.exists():
            return {}

        encoding = (
            self.config.get("env_file_encoding", "utf-8") if self.config else "utf-8"
        )
        try:
            with path.open("r", encoding=encoding) as f:
                data = yaml.safe_load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            # 可以选择记录日志
            print(f"Warning: Failed to load config file {config_file}: {e}")
            return {}


class RedisSettings(BaseModel):
    mode: str = "standalone"  # standalone, sentinel, cluster
    url: str = "redis://localhost:6379/0"  # For standalone
    nodes: str = ""  # comma separated "host:port", for cluster/sentinel
    master_name: str = "mymaster"  # For sentinel
    password: str = ""
    prefix: str = "fastapi-admin:"
    socket_timeout: int = 5
    max_connections: int = 10


class CaptchaSettings(BaseModel):
    enabled: bool = True
    ttl_seconds: int = 300
    length: int = 4
    max_attempts: int = 5


class LoggingSettings(BaseModel):
    """日志配置

    简化配置项, 直接控制日志文件保留时间和大小:
    - retention_days: 旧日志文件保留天数
    - max_bytes: 每个日志文件的最大最大大小(字节)
    """

    level: str = "INFO"
    console_enabled: bool = True
    file_enabled: bool = True
    directory: str = "logs"
    filename: str = "app.log"
    format: str = (
        "{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {name}:{function}:{line} | "
        "rid={extra[request_id]} uid={extra[user_id]} ip={extra[ip]} | {message}"
    )
    datefmt: str = "%Y-%m-%d %H:%M:%S"
    retention: str = "30 days"  # 旧日志保留天数
    rotation: str = "100 MB"  # 每个日志文件100MB


class Settings(BaseSettings):
    app_name: str = "FastAPI-Admin"
    debug: bool = False
    expose_error_detail: bool = False
    database_url: str = ""
    secret_key: str = "change-me-in-production-environment-123456789012"
    access_token_expire_minutes: int = 30
    refresh_token_expire_minutes: int = 60 * 24 * 7
    algorithm: str = "HS256"
    token_issuer: str = "FastAPI-Admin"
    token_audience: str = "FastAPI-Admin"
    snowflake_node_id: int = 0
    snowflake_epoch_ms: int = 1767196800000

    redis: RedisSettings = Field(default_factory=RedisSettings)
    captcha: CaptchaSettings = Field(default_factory=CaptchaSettings)
    log: LoggingSettings = Field(default_factory=LoggingSettings)

    @model_validator(mode="after")
    def _sync_policy_cache_compat(self) -> "Settings":
        fields_set = getattr(self, "__pydantic_fields_set__", set())
        if "policy_cache" in fields_set:
            return self

        return self

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        env_nested_delimiter="__",  # Allow REDIS__MODE=...
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: type[BaseSettings],
        init_settings: InitSettingsSource,
        env_settings: EnvSettingsSource,
        dotenv_settings: DotEnvSettingsSource,
        file_secret_settings: SecretsSettingsSource,
    ) -> tuple[PydanticBaseSettingsSource, ...]:
        return (
            init_settings,
            env_settings,
            dotenv_settings,
            YamlConfigSettingsSource(settings_cls),
            file_secret_settings,
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
