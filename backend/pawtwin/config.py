from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Process configuration for the local scaffold and future AWS adapter mode."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    mode: Literal["local", "aws"] = Field(default="local", validation_alias="PAWTWIN_MODE")
    bedrock_model_id: str | None = Field(default=None, validation_alias="BEDROCK_MODEL_ID")
    aws_region: str | None = Field(default=None, validation_alias="AWS_REGION")
    dynamodb_table_name: str | None = Field(
        default=None,
        validation_alias="DYNAMODB_TABLE_NAME",
    )
    agentcore_memory_id: str | None = Field(
        default=None,
        validation_alias="AGENTCORE_MEMORY_ID",
    )

    @model_validator(mode="after")
    def require_aws_configuration(self) -> "Settings":
        if self.mode != "aws":
            return self

        required = {
            "BEDROCK_MODEL_ID": self.bedrock_model_id,
            "AWS_REGION": self.aws_region,
            "DYNAMODB_TABLE_NAME": self.dynamodb_table_name,
            "AGENTCORE_MEMORY_ID": self.agentcore_memory_id,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"AWS mode requires: {', '.join(missing)}")
        return self

    @property
    def aws_connected(self) -> bool:
        """AWS connectivity remains false until real adapters are implemented."""

        return False
