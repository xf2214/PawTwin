from typing import Any

from pydantic import TypeAdapter
from pydantic.json_schema import models_json_schema

from pawtwin.config import Settings
from pawtwin.main import create_app
from pawtwin.models import Action, ApprovalIn, EventIn, FeedbackIn, Proposal, Receipt, RunState

DOMAIN_MODELS = (EventIn, Action, Proposal, ApprovalIn, FeedbackIn, Receipt)


def build_openapi_schema() -> dict[str, Any]:
    offline_settings = Settings(mode="local", _env_file=None)
    return create_app(offline_settings).openapi()


def build_domain_schema() -> dict[str, Any]:
    _, schema = models_json_schema(
        [(model, "validation") for model in DOMAIN_MODELS],
        title="PawTwin Domain Models",
    )
    schema["$defs"]["RunState"] = TypeAdapter(RunState).json_schema(mode="validation")
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    return schema
