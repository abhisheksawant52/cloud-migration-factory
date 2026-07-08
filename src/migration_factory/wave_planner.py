"""Wave planning: group servers into dependency-ordered migration waves.

The :class:`WavePlanner` performs a topological sort over the dependency graph
so that a server is never scheduled before the servers it depends on. Within
that ordering, servers are packed into waves no larger than ``max_wave_size``.
Servers marked ``RETIRE`` or ``RETAIN`` are excluded from the plan.
"""

from __future__ import annotations

import logging

from migration_factory.models import Disposition, Server, Wave

logger = logging.getLogger(__name__)


class WavePlanningError(RuntimeError):
    """Raised when a valid wave plan cannot be produced."""


class WavePlanner:
    """Group servers into ordered waves respecting dependencies.

    Args:
        max_wave_size: Maximum number of servers permitted in a single wave.

    Raises:
        ValueError: If ``max_wave_size`` is not a positive integer.
    """

    def __init__(self, max_wave_size: int = 10) -> None:
        if max_wave_size < 1:
            raise ValueError("max_wave_size must be a positive integer")
        self.max_wave_size = max_wave_size

    def _migratable(self, servers: list[Server]) -> list[Server]:
        """Return only servers whose disposition implies an actual migration."""
        excluded = {Disposition.RETIRE, Disposition.RETAIN}
        return [s for s in servers if s.disposition not in excluded]

    def _topological_order(self, servers: list[Server]) -> list[str]:
        """Return server IDs ordered so dependencies precede dependents.

        Uses Kahn's algorithm. Dependencies pointing at servers outside the
        migratable set are ignored so external/retained systems do not block
        the plan.

        Raises:
            WavePlanningError: If a dependency cycle is detected.
        """
        ids = {s.id for s in servers}
        # Restrict edges to servers present in the plan.
        deps: dict[str, set[str]] = {
            s.id: {d for d in s.dependencies if d in ids} for s in servers
        }
        dependents: dict[str, set[str]] = {sid: set() for sid in ids}
        for sid, sdeps in deps.items():
            for d in sdeps:
                dependents[d].add(sid)

        indegree = {sid: len(sdeps) for sid, sdeps in deps.items()}
        # Deterministic ordering: process ready nodes sorted by ID.
        ready = sorted(sid for sid, deg in indegree.items() if deg == 0)
        order: list[str] = []

        while ready:
            current = ready.pop(0)
            order.append(current)
            newly_ready: list[str] = []
            for dependent in dependents[current]:
                indegree[dependent] -= 1
                if indegree[dependent] == 0:
                    newly_ready.append(dependent)
            # Keep the ready list sorted for stable output.
            ready = sorted(ready + newly_ready)

        if len(order) != len(ids):
            unresolved = ids - set(order)
            raise WavePlanningError(
                f"Dependency cycle detected among servers: {sorted(unresolved)}"
            )
        return order

    def plan(self, servers: list[Server]) -> list[Wave]:
        """Produce an ordered list of waves for the given servers.

        Args:
            servers: Servers to plan, typically already assessed.

        Returns:
            A list of :class:`Wave` objects in migration order. Each server's
            ``wave_id`` field is set to the wave it was assigned to.

        Raises:
            WavePlanningError: If the dependency graph contains a cycle.
        """
        migratable = self._migratable(servers)
        if not migratable:
            logger.info("No migratable servers; returning empty plan")
            return []

        by_id = {s.id: s for s in migratable}
        order = self._topological_order(migratable)

        waves: list[Wave] = []
        for index in range(0, len(order), self.max_wave_size):
            chunk = order[index : index + self.max_wave_size]
            sequence = len(waves)
            wave = Wave(
                id=f"wave-{sequence + 1}",
                name=f"Wave {sequence + 1}",
                server_ids=list(chunk),
                sequence=sequence,
            )
            for sid in chunk:
                by_id[sid].wave_id = wave.id
            waves.append(wave)

        logger.info(
            "Planned %d server(s) into %d wave(s)", len(order), len(waves)
        )
        return waves
