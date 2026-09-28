from typing import Literal

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ModelBackend = Literal["inline", "local_fake", "bedrock"]
WorkerMode = Literal["inline", "background"]
MemoryBackend = Literal["not_implemented", "agentcore"]


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
    database_path: str | None = Field(default=None, validation_alias="PAWTWIN_DB_PATH")
    # Non-secret LOCAL demo gate. The real judge passphrase is supplied via the
    # PAWTWIN_DEMO_PASSPHRASE environment variable and private test
    # instructions; it is never committed to source or shipped in the frontend.
    demo_passphrase: str = Field(
        default="local-demo-passphrase",
        validation_alias="PAWTWIN_DEMO_PASSPHRASE",
    )

    # --- Day-2: analyzer backend, worker and reliability budgets --------------
    # ``model_backend`` is decoupled from ``mode`` (ruling 15) so a real Bedrock
    # model can be exercised while storage is still local SQLite. Left unset it is
    # derived from ``mode``; ``inline`` is only ever an explicit TEST backend.
    model_backend: ModelBackend | None = Field(
        default=None,
        validation_alias="PAWTWIN_MODEL_BACKEND",
    )
    # Day-3 (ruling 10): the long-term-memory backend, decoupled from ``mode``
    # exactly like ``model_backend``. Left unset it is derived from ``mode``
    # (local -> not_implemented, aws -> agentcore). ``not_implemented`` NEVER
    # fabricates retrieved memory; ``agentcore`` is the real adapter and requires
    # AGENTCORE_MEMORY_ID (enforced in ``require_aws_configuration``).
    memory_backend: MemoryBackend | None = Field(
        default=None,
        validation_alias="PAWTWIN_MEMORY_BACKEND",
    )
    # Default ``inline`` keeps request-time analysis (and therefore the frozen
    # baseline tests and the offline contract export) deterministic; ``background``
    # is enabled explicitly by the e2e server and by production.
    worker_mode: WorkerMode = Field(default="inline", validation_alias="PAWTWIN_WORKER_MODE")
    analysis_timeout_seconds: float = Field(
        default=45.0,
        gt=0,
        validation_alias="PAWTWIN_ANALYSIS_TIMEOUT_SECONDS",
    )
    max_model_calls_per_run: int = Field(
        default=4,
        gt=0,
        validation_alias="PAWTWIN_MAX_MODEL_CALLS",
    )
    max_output_tokens: int = Field(
        default=800,
        gt=0,
        validation_alias="PAWTWIN_MAX_OUTPUT_TOKENS",
    )
    lease_seconds: int = Field(default=60, gt=0, validation_alias="PAWTWIN_LEASE_SECONDS")
    lease_renew_seconds: int = Field(
        default=15,
        gt=0,
        validation_alias="PAWTWIN_LEASE_RENEW_SECONDS",
    )
    max_attempts: int = Field(default=2, gt=0, validation_alias="PAWTWIN_MAX_ATTEMPTS")
    # Concurrency ceilings from the five-day spec: one analysis per login session,
    # two site-wide. Enforced IN-PROCESS only on Day-2; a cross-replica ceiling
    # needs database-level counting and is deferred.
    max_concurrent_per_session: int = Field(
        default=1,
        gt=0,
        validation_alias="PAWTWIN_MAX_CONCURRENT_PER_SESSION",
    )
    max_concurrent_global: int = Field(
        default=2,
        gt=0,
        validation_alias="PAWTWIN_MAX_CONCURRENT_GLOBAL",
    )

    @property
    def effective_model_backend(self) -> ModelBackend:
        """Resolve the analyzer backend; never silently becomes a stand-in."""

        if self.model_backend is not None:
            return self.model_backend
        return "bedrock" if self.mode == "aws" else "local_fake"

    @property
    def effective_memory_backend(self) -> MemoryBackend:
        """Resolve the memory backend; never silently becomes a stand-in.

        ``not_implemented`` is the honest local default: feedback is saved to the
        business database and long-term extraction/retrieval simply does not run,
        so ``search_owner_memory`` returns nothing rather than a fabricated memory.
        """

        if self.memory_backend is not None:
            return self.memory_backend
        return "agentcore" if self.mode == "aws" else "not_implemented"

    @model_validator(mode="after")
    def require_aws_configuration(self) -> "Settings":
        if self.mode != "aws":
            # A real model backend always needs its target model and region, even
            # while storage is still local SQLite (ruling 15).
            if self.effective_model_backend == "bedrock":
                missing = [
                    name
                    for name, value in (
                        ("BEDROCK_MODEL_ID", self.bedrock_model_id),
                        ("AWS_REGION", self.aws_region),
                    )
                    if not value
                ]
                if missing:
                    raise ValueError(f"model_backend=bedrock requires: {', '.join(missing)}")
            # Day-3 (ruling 10): the same decoupling for memory -- a real AgentCore
            # backend needs its memory id and region even while storage is local.
            if self.effective_memory_backend == "agentcore":
                missing = [
                    name
                    for name, value in (
                        ("AGENTCORE_MEMORY_ID", self.agentcore_memory_id),
                        ("AWS_REGION", self.aws_region),
                    )
                    if not value
                ]
                if missing:
                    raise ValueError(f"memory_backend=agentcore requires: {', '.join(missing)}")
            return self

        # AWS mode must never be paired with a stand-in analyzer (AGENTS.md).
        if self.model_backend is not None and self.model_backend != "bedrock":
            raise ValueError("PAWTWIN_MODE=aws requires PAWTWIN_MODEL_BACKEND=bedrock")
        # ...nor with unimplemented memory: aws mode claims a real AgentCore store.
        if self.memory_backend is not None and self.memory_backend != "agentcore":
            raise ValueError("PAWTWIN_MODE=aws requires PAWTWIN_MEMORY_BACKEND=agentcore")

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

    @model_validator(mode="after")
    def validate_budget_ordering(self) -> "Settings":
        if self.lease_renew_seconds >= self.lease_seconds:
            raise ValueError("PAWTWIN_LEASE_RENEW_SECONDS must be shorter than the lease")
        if self.max_concurrent_per_session > self.max_concurrent_global:
            raise ValueError("per-session concurrency cannot exceed the site-wide ceiling")
        return self

    @property
    def aws_connected(self) -> bool:
        """True only when storage AND model AND memory are all really connected.

        Storage is still SQLite (the DynamoDB adapter is not implemented), so this
        stays False even with ``analyzer='bedrock'`` and ``memory='agentcore'``:
        the UI shows each label separately and never claims a cloud connection that
        has not been verified end to end.
        """

        return False
