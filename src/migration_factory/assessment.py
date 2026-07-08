"""Assessment: turn a raw inventory into disposition recommendations.

The :class:`Assessor` applies a small, deterministic rule set to each server to
recommend one of the 6 Rs and to compute a 0-100 *readiness score* describing
how straightforward the workload is expected to be to migrate.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable

from migration_factory.models import Disposition, Server

logger = logging.getLogger(__name__)

# Operating systems that are end-of-life and generally cannot be lifted as-is.
_END_OF_LIFE_OS = ("windows server 2003", "windows server 2008", "centos 6")

# Substrings that hint a workload has a managed-service equivalent.
_REPLATFORM_HINTS = ("sql", "postgres", "mysql", "oracle", "mongo", "redis")


class AssessmentResult:
    """The outcome of assessing a single server.

    Attributes:
        server: The server, with its ``disposition`` field populated.
        readiness_score: A 0-100 score; higher means easier to migrate.
        rationale: Human-readable reasons behind the recommendation.
    """

    def __init__(
        self, server: Server, readiness_score: int, rationale: list[str]
    ) -> None:
        self.server = server
        self.readiness_score = readiness_score
        self.rationale = rationale

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return (
            f"AssessmentResult(server={self.server.id!r}, "
            f"disposition={self.server.disposition}, "
            f"readiness_score={self.readiness_score})"
        )


class Assessor:
    """Compute disposition recommendations and readiness scores.

    Args:
        idle_cpu_threshold: A server with ``cpu`` at or below this value is
            considered a retirement candidate.
    """

    def __init__(self, idle_cpu_threshold: int = 0) -> None:
        self.idle_cpu_threshold = idle_cpu_threshold

    def recommend_disposition(self, server: Server) -> tuple[Disposition, list[str]]:
        """Recommend one of the 6 Rs for a single server.

        Args:
            server: The server to assess.

        Returns:
            A tuple of the recommended :class:`Disposition` and a list of
            human-readable rationale strings.
        """
        rationale: list[str] = []
        os_lower = server.os.lower()

        if server.cpu <= self.idle_cpu_threshold:
            rationale.append("No allocated vCPU; likely decommissioned already.")
            return Disposition.RETIRE, rationale

        if any(eol in os_lower for eol in _END_OF_LIFE_OS):
            rationale.append(f"Operating system '{server.os}' is end-of-life.")
            return Disposition.REFACTOR, rationale

        if any(hint in os_lower for hint in _REPLATFORM_HINTS):
            rationale.append("Workload has a managed-service equivalent.")
            return Disposition.REPLATFORM, rationale

        if len(server.dependencies) > 5:
            rationale.append("Highly coupled workload; re-architecture advised.")
            return Disposition.REFACTOR, rationale

        rationale.append("Standard workload suitable for lift-and-shift.")
        return Disposition.REHOST, rationale

    def readiness_score(self, server: Server, disposition: Disposition) -> int:
        """Score how ready a server is to migrate, from 0 to 100.

        The score starts high and is reduced by risk factors such as heavy
        dependency coupling, end-of-life operating systems, and strategies
        (refactor) that require more engineering effort.

        Args:
            server: The server being scored.
            disposition: The recommended disposition for the server.

        Returns:
            An integer readiness score clamped to the ``0..100`` range.
        """
        score = 100

        # Coupling penalty: 8 points per dependency, capped at 40.
        score -= min(len(server.dependencies) * 8, 40)

        # Effort penalty by strategy.
        effort = {
            Disposition.REHOST: 0,
            Disposition.REPLATFORM: 15,
            Disposition.REFACTOR: 35,
            Disposition.REPURCHASE: 25,
            Disposition.RETIRE: 0,
            Disposition.RETAIN: 10,
        }
        score -= effort.get(disposition, 0)

        # End-of-life OS penalty.
        if any(eol in server.os.lower() for eol in _END_OF_LIFE_OS):
            score -= 20

        return max(0, min(100, score))

    def assess_server(self, server: Server) -> AssessmentResult:
        """Assess a single server, mutating its ``disposition`` field.

        Args:
            server: The server to assess.

        Returns:
            The :class:`AssessmentResult` for the server.
        """
        disposition, rationale = self.recommend_disposition(server)
        server.disposition = disposition
        score = self.readiness_score(server, disposition)
        logger.debug(
            "Assessed %s: %s (readiness=%d)", server.id, disposition.value, score
        )
        return AssessmentResult(server=server, readiness_score=score, rationale=rationale)

    def assess_inventory(self, inventory: Iterable[dict]) -> list[AssessmentResult]:
        """Assess a full inventory supplied as a list of server dicts.

        Args:
            inventory: An iterable of mappings that validate as :class:`Server`.

        Returns:
            One :class:`AssessmentResult` per input server.
        """
        results = [self.assess_server(Server.model_validate(item)) for item in inventory]
        logger.info("Assessed %d server(s)", len(results))
        return results
