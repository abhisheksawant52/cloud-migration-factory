"""Unit tests for the disposition and readiness logic."""

from __future__ import annotations

from migration_factory.assessment import Assessor
from migration_factory.models import Disposition, Server


def _server(**overrides) -> Server:
    base = {"id": "s1", "hostname": "host1", "os": "Ubuntu 22.04", "cpu": 4, "memory_gb": 16}
    base.update(overrides)
    return Server.model_validate(base)


def test_idle_server_is_retired() -> None:
    assessor = Assessor(idle_cpu_threshold=0)
    disposition, _ = assessor.recommend_disposition(_server(cpu=0))
    assert disposition is Disposition.RETIRE


def test_end_of_life_os_is_refactored() -> None:
    assessor = Assessor()
    disposition, _ = assessor.recommend_disposition(_server(os="Windows Server 2008 R2"))
    assert disposition is Disposition.REFACTOR


def test_database_workload_is_replatformed() -> None:
    assessor = Assessor()
    disposition, _ = assessor.recommend_disposition(_server(os="MySQL 8 on Debian"))
    assert disposition is Disposition.REPLATFORM


def test_standard_workload_is_rehosted() -> None:
    assessor = Assessor()
    disposition, _ = assessor.recommend_disposition(_server())
    assert disposition is Disposition.REHOST


def test_readiness_score_penalises_dependencies_and_effort() -> None:
    assessor = Assessor()
    simple = _server()
    coupled = _server(dependencies=["a", "b", "c"])
    assert assessor.readiness_score(simple, Disposition.REHOST) == 100
    assert assessor.readiness_score(
        coupled, Disposition.REFACTOR
    ) < assessor.readiness_score(simple, Disposition.REHOST)


def test_assess_inventory_sets_disposition() -> None:
    assessor = Assessor()
    results = assessor.assess_inventory(
        [{"id": "s1", "hostname": "h", "os": "Ubuntu 22.04", "cpu": 2, "memory_gb": 8}]
    )
    assert results[0].server.disposition is Disposition.REHOST
    assert 0 <= results[0].readiness_score <= 100
