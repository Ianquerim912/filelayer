from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import AliasChoices, Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from .exceptions import StorageConfigurationError


class StorageSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    provider: Literal["local", "s3"] = Field(
        ...,
        validation_alias=AliasChoices("STORAGE_PROVIDER"),
    )

    default_prefix: str = Field(
        default="",
        validation_alias=AliasChoices("STORAGE_DEFAULT_PREFIX"),
    )

    encoding: str = Field(
        default="utf-8",
        validation_alias=AliasChoices("STORAGE_ENCODING"),
    )

    local_base_path: Path = Field(
        default=Path("./data/storage"),
        validation_alias=AliasChoices("LOCAL_STORAGE_BASE_PATH"),
    )

    s3_endpoint_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_ENDPOINT_URL"),
    )
    s3_access_key_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_ACCESS_KEY_ID"),
    )
    s3_secret_access_key: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_SECRET_ACCESS_KEY"),
    )
    s3_session_token: SecretStr | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_SESSION_TOKEN"),
    )
    s3_region_name: str = Field(
        default="us-east-1",
        validation_alias=AliasChoices("S3_REGION_NAME", "AWS_DEFAULT_REGION"),
    )
    s3_bucket: str | None = Field(
        default=None,
        validation_alias=AliasChoices("S3_BUCKET", "S3_BUCKET_NAME"),
    )
    s3_use_ssl: bool = Field(
        default=True,
        validation_alias=AliasChoices("S3_USE_SSL"),
    )
    s3_verify_ssl: bool = Field(
        default=True,
        validation_alias=AliasChoices("S3_VERIFY_SSL"),
    )
    s3_addressing_style: Literal["virtual", "path", "auto"] = Field(
        default="virtual",
        validation_alias=AliasChoices("S3_ADDRESSING_STYLE"),
    )
    s3_connect_timeout: int = Field(
        default=10,
        validation_alias=AliasChoices("S3_CONNECT_TIMEOUT"),
    )
    s3_read_timeout: int = Field(
        default=60,
        validation_alias=AliasChoices("S3_READ_TIMEOUT"),
    )
    s3_max_attempts: int = Field(
        default=5,
        validation_alias=AliasChoices("S3_MAX_ATTEMPTS"),
    )

    @field_validator("default_prefix")
    @classmethod
    def normalize_default_prefix(cls, value: str) -> str:
        return value.strip("/")

    @field_validator("local_base_path")
    @classmethod
    def normalize_local_base_path(cls, value: Path) -> Path:
        return value.expanduser()

    @model_validator(mode="after")
    def validate_provider_settings(self) -> "StorageSettings":
        if self.provider == "s3":
            missing: list[str] = []

            if not self.s3_access_key_id:
                missing.append("S3_ACCESS_KEY_ID")
            if not self.s3_secret_access_key:
                missing.append("S3_SECRET_ACCESS_KEY")
            if not self.s3_bucket:
                missing.append("S3_BUCKET")

            if missing:
                raise StorageConfigurationError(
                    "Missing required S3 settings: " + ", ".join(missing)
                )

        return self

    @property
    def s3_secret_access_key_value(self) -> str | None:
        return (
            self.s3_secret_access_key.get_secret_value()
            if self.s3_secret_access_key
            else None
        )

    @property
    def s3_session_token_value(self) -> str | None:
        return (
            self.s3_session_token.get_secret_value()
            if self.s3_session_token
            else None
        )
