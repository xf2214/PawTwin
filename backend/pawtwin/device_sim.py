"""Explicitly simulated actuator.

Always labelled ``simulated=True``; never pretends to be real hardware. The
command id is fixed by the caller (derived from run + proposal version) so a
retry reuses the same id and the repository can keep accounting idempotent.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from pawtwin.models import Action, Receipt

DeviceMode = Literal["succeeded", "failed", "unknown"]


class DeviceSimulator:
    """Simulated feeder. ``mode`` is injectable for demos/tests (Day-2 endpoint)."""

    def __init__(self, mode: DeviceMode = "succeeded") -> None:
        self._mode: DeviceMode = mode

    @property
    def mode(self) -> DeviceMode:
        return self._mode

    def set_mode(self, mode: DeviceMode) -> None:
        self._mode = mode

    def execute(self, command_id: UUID, action: Action) -> Receipt:
        # The action is acknowledged but no real device is driven; the receipt
        # status reflects the injected simulation mode, not a hardware result.
        _ = action
        return Receipt(command_id=command_id, status=self._mode, simulated=True)
