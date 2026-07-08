"""Application configuration via pydantic-settings.

Settings are read from the environment (optionally from a ``.env`` file) using
the ``MIGRATION_FACTORY_`` prefix, e.g. ``MIGRATION_FACTORY_LOG_LEVEL=DEBUG``.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the migration factory."""

    model_config = SettingsConfigDict(
        env_prefix="MIGRATION_FACTORY_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = Field(
        default="INFO",
        description="Root logging level (DEBUG, INFO, WARNING, ERROR).",
    )
    log_json: bool = Field(
        default=False,
        description="Emit logs as single-line JSON when true.",
    )
    max_wave_size: int = Field(
        default=10,
        ge=1,
        description="Default maximum number of servers per migration wave.",
    )
    idle_cpu_threshold: int = Field(
        default=0,
        ge=0,
        description="Servers with vCPU at or below this are retirement candidates.",
    )
    artifact_bucket: str = Field(
        default="migration-factory-artifacts",
        description="S3 bucket that stores inventory and plan artifacts.",
    )
    state_table: str = Field(
        default="migration-factory-state",
        description="DynamoDB table that stores migration task state.",
    )
    aws_region: str = Field(
        default="us-east-1",
        description="AWS region for the factory's deployment infrastructure.",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached :class:`Settings` instance."""
    return Settings()
