"""OFFLINE guards for the DynamoDB adapter (Day-5 ruling 6).

There is deliberately NO moto and NO mock anywhere: a SQLite or stubbed PASS never
stands in for the real conditional-write / transaction semantics (five-day spec
L106). Offline we assert only two things that need no account and no table:

1. ``DynamoRepository``'s public method set COVERS the ``Repository`` protocol, so
   a future protocol method cannot be silently un-implemented (a missing-method
   guard -- explicitly NOT cloud evidence);
2. the parts of the adapter that fail closed BEFORE any boto3 call: the empty table
   name and the ruling-11 ``available`` invariant (which raises ``ValueError`` ahead
   of touching the network, so it is checkable offline).

Every behavioural test lives in ``test_repo_dynamo_live.py`` behind the
``dynamodb_live`` marker and only runs against a REAL provisioned table.
"""

from __future__ import annotations

from uuid import uuid4

import pytest
from pawtwin.repo_dynamo import DynamoRepository, DynamoUnavailable
from pawtwin.repository import Repository


def _public_methods(cls: type) -> set[str]:
    return {
        name
        for name in dir(cls)
        if not name.startswith("_") and callable(getattr(cls, name, None))
    }


def test_dynamo_repository_covers_the_whole_repository_protocol() -> None:
    """Missing-method guard: the adapter must implement every protocol method.

    This is a STATIC coverage check, not cloud evidence -- it proves nothing about
    whether the DynamoDB conditional writes actually behave like SQLite on a real
    table (that is ``test_repo_dynamo_live.py``, skipped without credentials).
    """

    protocol_methods = _public_methods(Repository)
    adapter_methods = _public_methods(DynamoRepository)
    missing = protocol_methods - adapter_methods
    assert missing == set(), f"DynamoRepository is missing protocol methods: {sorted(missing)}"
    # ``close`` is not on the protocol but main.py's lifespan calls it on every
    # repository, so the adapter must expose it too.
    assert "close" in adapter_methods


def test_empty_table_name_fails_closed_instead_of_guessing() -> None:
    with pytest.raises(DynamoUnavailable, match="DYNAMODB_TABLE_NAME_MISSING"):
        DynamoRepository("")


def test_available_without_record_ids_raises_before_any_cloud_call() -> None:
    """Ruling-11 invariant, offline: the ``ValueError`` is raised ahead of any boto3
    client construction, so it needs no credentials -- and it is the negative half
    of "``available`` is only ever written with real AgentCore record ids".
    Constructing the adapter is lazy, so this never touches the network.
    """

    repo = DynamoRepository("never-contacted-table")
    with pytest.raises(ValueError, match="requires memory_record_ids"):
        repo.set_feedback_status(uuid4(), memory_status="available")
    with pytest.raises(ValueError, match="requires memory_record_ids"):
        repo.set_feedback_status(uuid4(), memory_status="available", memory_record_ids=[])
