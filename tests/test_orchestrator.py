"""Unit tests for the migration orchestrator state machine."""

from __future__ import annotations

import pytest

from migration_factory import __version__
from migration_factory.models import Server, TaskStatus
from migration_factory.orchestrator import InvalidTransitionError, MigrationOrchestrator


def _server(sid: str = "s1") -> Server:
    return Server(id=sid, hostname=sid, os="Ubuntu 22.04", cpu=2, memory_gb=8)


def test_version_is_exposed() -> None:
    assert __version__ == "0.1.0"


def test_happy_path_advances_to_complete() -> None:
    orch = MigrationOrchestrator()
    task = orch.create_task(_server())
    for _ in range(4):
        orch.advance(task.id)
    assert task.status is TaskStatus.COMPLETE


def test_invalid_transition_is_rejected() -> None:
    orch = MigrationOrchestrator()
    task = orch.create_task(_server())
    with pytest.raises(InvalidTransitionError):
        orch.transition(task.id, TaskStatus.CUTOVER)


def test_advance_on_terminal_task_raises() -> None:
    orch = MigrationOrchestrator()
    task = orch.create_task(_server())
    orch.transition(task.id, TaskStatus.FAILED)
    with pytest.raises(InvalidTransitionError):
        orch.advance(task.id)


def test_duplicate_task_creation_raises() -> None:
    orch = MigrationOrchestrator()
    orch.create_task(_server())
    with pytest.raises(ValueError):
        orch.create_task(_server())


def test_summary_counts_by_status() -> None:
    orch = MigrationOrchestrator()
    t1 = orch.create_task(_server("a"))
    orch.create_task(_server("b"))
    orch.advance(t1.id)
    assert orch.summary() == {"pending": 1, "replicating": 1}
