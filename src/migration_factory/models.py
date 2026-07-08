"""Domain models for the cloud migration factory.

The models are Pydantic v2 models so they can be validated when read from and
written to JSON inventory files. They intentionally contain no infrastructure
logic — that lives in :mod:`assessment`, :mod:`wave_planner`, and
:mod:`orchestrator`.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class Disposition(str, Enum):
    """The "6 Rs" migration strategies for a workload.

    Each value describes how a server or application should be treated when it
    is migrated to the cloud.
    """

    REHOST = "rehost"
    """Lift-and-shift onto equivalent cloud infrastructure."""

    REPLATFORM = "replatform"
    """Lift-and-reshape (e.g. move a database onto a managed service)."""

    REFACTOR = "refactor"
    """Re-architect the workload to be cloud-native."""

    RETIRE = "retire"
    """Decommission the workload; it is no longer needed."""

    RETAIN = "retain"
    """Keep the workload where it is for now."""

    REPURCHASE = "repurchase"
    """Replace with a different product (typically SaaS)."""


class TaskStatus(str, Enum):
    """Lifecycle states for a :class:`MigrationTask`.

    The happy-path transition order is
    ``PENDING -> REPLICATING -> TESTING -> CUTOVER -> COMPLETE``. A task may be
    marked ``FAILED`` from any active state.
    """

    PENDING = "pending"
    REPLICATING = "replicating"
    TESTING = "testing"
    CUTOVER = "cutover"
    COMPLETE = "complete"
    FAILED = "failed"


class Server(BaseModel):
    """A discovered server in the source estate."""

    id: str = Field(..., description="Stable unique identifier for the server.")
    hostname: str = Field(..., description="Fully qualified or short host name.")
    os: str = Field(..., description="Operating system name and version.")
    cpu: int = Field(..., ge=0, description="Number of vCPUs.")
    memory_gb: float = Field(..., ge=0, description="Memory in gibibytes.")
    dependencies: list[str] = Field(
        default_factory=list,
        description="IDs of other servers this server depends on.",
    )
    disposition: Disposition | None = Field(
        default=None,
        description="Recommended migration strategy; set by the Assessor.",
    )
    wave_id: str | None = Field(
        default=None,
        description="ID of the wave this server has been planned into.",
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current migration status of the server.",
    )


class Application(BaseModel):
    """A business application composed of one or more servers."""

    id: str = Field(..., description="Stable unique identifier for the application.")
    name: str = Field(..., description="Human-readable application name.")
    server_ids: list[str] = Field(
        default_factory=list,
        description="IDs of servers that make up this application.",
    )
    criticality: int = Field(
        default=3,
        ge=1,
        le=5,
        description="Business criticality on a 1 (low) to 5 (critical) scale.",
    )


class Wave(BaseModel):
    """A batch of servers scheduled to migrate together."""

    id: str = Field(..., description="Stable unique identifier for the wave.")
    name: str = Field(..., description="Human-readable wave name.")
    server_ids: list[str] = Field(
        default_factory=list,
        description="IDs of servers assigned to this wave, in migration order.",
    )
    sequence: int = Field(
        ..., ge=0, description="Zero-based ordering of the wave in the plan."
    )


class MigrationTask(BaseModel):
    """A unit of migration work tracked by the orchestrator."""

    id: str = Field(..., description="Stable unique identifier for the task.")
    server_id: str = Field(..., description="ID of the server being migrated.")
    wave_id: str | None = Field(
        default=None, description="ID of the wave this task belongs to."
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING, description="Current lifecycle state."
    )
    notes: list[str] = Field(
        default_factory=list,
        description="Chronological free-text notes recorded during migration.",
    )
