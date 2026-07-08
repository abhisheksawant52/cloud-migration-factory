"""Unit tests for dependency-ordered wave planning."""

from __future__ import annotations

import pytest

from migration_factory.models import Disposition, Server
from migration_factory.wave_planner import WavePlanner, WavePlanningError


def _server(sid: str, deps: list[str] | None = None, disp=Disposition.REHOST) -> Server:
    return Server(
        id=sid,
        hostname=sid,
        os="Ubuntu 22.04",
        cpu=2,
        memory_gb=8,
        dependencies=deps or [],
        disposition=disp,
    )


def test_dependencies_precede_dependents() -> None:
    servers = [_server("app", deps=["db"]), _server("db")]
    planner = WavePlanner(max_wave_size=10)
    waves = planner.plan(servers)
    order = [sid for wave in waves for sid in wave.server_ids]
    assert order.index("db") < order.index("app")


def test_max_wave_size_is_respected() -> None:
    servers = [_server(f"s{i}") for i in range(5)]
    planner = WavePlanner(max_wave_size=2)
    waves = planner.plan(servers)
    assert [len(w.server_ids) for w in waves] == [2, 2, 1]
    assert [w.sequence for w in waves] == [0, 1, 2]


def test_retired_servers_are_excluded() -> None:
    servers = [_server("keep"), _server("drop", disp=Disposition.RETIRE)]
    planner = WavePlanner()
    waves = planner.plan(servers)
    planned = {sid for wave in waves for sid in wave.server_ids}
    assert planned == {"keep"}


def test_wave_id_is_assigned_to_servers() -> None:
    servers = [_server("a"), _server("b")]
    WavePlanner(max_wave_size=1).plan(servers)
    assert {s.wave_id for s in servers} == {"wave-1", "wave-2"}


def test_dependency_cycle_raises() -> None:
    servers = [_server("a", deps=["b"]), _server("b", deps=["a"])]
    with pytest.raises(WavePlanningError):
        WavePlanner().plan(servers)


def test_invalid_max_wave_size_raises() -> None:
    with pytest.raises(ValueError):
        WavePlanner(max_wave_size=0)
