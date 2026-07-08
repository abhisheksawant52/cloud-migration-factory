"""migration_factory — assess, plan, and orchestrate cloud migrations.

A pure-Python library and CLI for running a cloud migration factory:

- ingest a server/application inventory and compute disposition
  recommendations (the 6 Rs) plus a readiness score (:mod:`assessment`),
- group workloads into dependency-ordered migration waves
  (:mod:`wave_planner`), and
- track migration tasks through their lifecycle (:mod:`orchestrator`).
"""

from migration_factory.models import (
    Application,
    Disposition,
    MigrationTask,
    Server,
    TaskStatus,
    Wave,
)

__version__ = "0.1.0"

__all__ = [
    "Application",
    "Disposition",
    "MigrationTask",
    "Server",
    "TaskStatus",
    "Wave",
    "__version__",
]
