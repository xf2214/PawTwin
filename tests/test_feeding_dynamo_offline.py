"""Inspect generated transaction guards only; no live AWS acceptance claim."""

from types import SimpleNamespace

from pawtwin.device_sim import DeviceSimulator
from pawtwin.models import Receipt, make_command_id
from pawtwin.repo_dynamo import DynamoRepository
from pawtwin.repo_sqlite import DEMO_OWNER_ID
from pawtwin.workflow import Workflow
from test_feeding_reservation import pending


def adapter(monkeypatch, facts):
    calls = []
    client = SimpleNamespace(
        transact_write_items=lambda **kwargs: calls.append(kwargs),
        exceptions=SimpleNamespace(TransactionCanceledException=RuntimeError),
    )
    cloud = DynamoRepository("offline-test", client=client)
    monkeypatch.setattr(cloud, "_ser_item", lambda value: value)
    monkeypatch.setattr(cloud, "_av", lambda value: value)
    monkeypatch.setattr(cloud, "_get", lambda key: facts)
    return cloud, calls


def test_old_dynamo_facts_without_a_guard_version_cannot_start_feeding(repo, monkeypatch):
    record = pending(Workflow(repo, DeviceSimulator()))
    cloud, calls = adapter(monkeypatch, vars(repo.get_facts(DEMO_OWNER_ID)))
    assert cloud.reserve_feeding(record) is False
    assert calls == []


def test_dynamo_reservation_binds_facts_gate_and_run_in_one_transaction(repo, monkeypatch):
    record = pending(Workflow(repo, DeviceSimulator()))
    facts = {**vars(repo.get_facts(DEMO_OWNER_ID)), "feeding_guard_version": 1}
    cloud, calls = adapter(monkeypatch, facts)
    assert cloud.reserve_feeding(record) is True
    operations = calls[0]["TransactItems"]
    assert len(operations) == 3
    assert "feeding_guard_version" in operations[0]["ConditionCheck"]["ConditionExpression"]
    assert operations[1]["Put"]["ConditionExpression"] == "attribute_not_exists(pk)"
    assert "proposal_version = :pv" in operations[2]["Update"]["ConditionExpression"]
    assert operations[2]["Update"]["ExpressionAttributeValues"][":owner"] == DEMO_OWNER_ID


def test_dynamo_unknown_receipt_updates_the_run_and_retains_its_gate(repo, monkeypatch):
    record = pending(Workflow(repo, DeviceSimulator()))
    cloud, calls = adapter(monkeypatch, {"owner_id": DEMO_OWNER_ID})
    monkeypatch.setattr(cloud, "_seed_facts", lambda owner: None)
    command = make_command_id(record.run_id, record.proposal_version)
    assert cloud.record_receipt_once(
        command_id=command,
        run_id=record.run_id,
        receipt=Receipt(command_id=command, status="unknown", simulated=True),
        dispense_grams=15,
    )
    operations = calls[0]["TransactItems"]
    assert len(operations) == 2
    assert operations[1]["Update"]["ExpressionAttributeValues"][":state"] == "unknown"
    assert all("Delete" not in operation for operation in operations)
