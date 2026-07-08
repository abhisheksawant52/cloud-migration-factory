"""Orchestration: track migration tasks through their lifecycle.

The :class:`MigrationOrchestrator` owns a set of :class:`MigrationTask` objects
and enforces the allowed state machine when advancing them:

``PENDING -> REPLICATING -> TESTING -> CUTOVER -> COMPLETE``

Any active (non-terminal) task may also transition to ``FAILED``.
"""

from __future__ import annotations

import logging

from migration_factory.models import MigrationTask, Server, TaskStatus

logger = logging.getLogger(__name__)

# Allowed forward transitions of the migration state machine.
_ALLOWED_TRANSITIONS: dict[TaskStatus, set[TaskStatus]] = {
    TaskStatus.PENDING: {TaskStatus.REPLICATING, TaskStatus.FAILED},
    TaskStatus.REPLICATING: {TaskStatus.TESTING, TaskStatus.FAILED},
    TaskStatus.TESTING: {TaskStatus.CUTOVER, TaskStatus.FAILED},
    TaskStatus.CUTOVER: {TaskStatus.COMPLETE, TaskStatus.FAILED},
    TaskStatus.COMPLETE: set(),
    TaskStatus.FAILED: set(),
}


class InvalidTransitionError(RuntimeError):
    """Raised when an illegal task state transition is attempted."""


class MigrationOrchestrator:
    """Create and advance migration tasks through their lifecycle."""

    def __init__(self) -> None:
        self._tasks: dict[str, MigrationTask] = {}

    @property
    def tasks(self) -> list[MigrationTask]:
        """All tasks known to the orchestrator, in creation order."""
        return list(self._tasks.values())

    def create_task(self, server: Server) -> MigrationTask:
        """Create a pending task for a server.

        Args:
            server: The server to migrate. Its ``wave_id`` is copied onto the
                task if present.

        Returns:
            The newly created :class:`MigrationTask`.

        Raises:
            ValueError: If a task already exists for the server.
        """
        task_id = f"task-{server.id}"
        if task_id in self._tasks:
            raise ValueError(f"Task already exists for server {server.id!r}")
        task = MigrationTask(
            id=task_id, server_id=server.id, wave_id=server.wave_id
        )
        self._tasks[task_id] = task
        logger.info("Created %s for server %s", task_id, server.id)
        return task

    def get_task(self, task_id: str) -> MigrationTask:
        """Return the task with the given ID.

        Raises:
            KeyError: If no such task exists.
        """
        return self._tasks[task_id]

    def transition(
        self, task_id: str, new_status: TaskStatus, note: str | None = None
    ) -> MigrationTask:
        """Move a task to ``new_status`` if the transition is allowed.

        Args:
            task_id: ID of the task to transition.
            new_status: The desired next status.
            note: Optional note appended to the task's history.

        Returns:
            The updated task.

        Raises:
            KeyError: If the task does not exist.
            InvalidTransitionError: If the transition is not permitted.
        """
        task = self._tasks[task_id]
        allowed = _ALLOWED_TRANSITIONS[task.status]
        if new_status not in allowed:
            raise InvalidTransitionError(
                f"Cannot transition {task_id} from {task.status.value} "
                f"to {new_status.value}"
            )
        previous = task.status
        task.status = new_status
        if note:
            task.notes.append(note)
        logger.info(
            "%s: %s -> %s", task_id, previous.value, new_status.value
        )
        return task

    def advance(self, task_id: str, note: str | None = None) -> MigrationTask:
        """Advance a task to the next status on the happy path.

        Args:
            task_id: ID of the task to advance.
            note: Optional note appended to the task's history.

        Returns:
            The updated task.

        Raises:
            InvalidTransitionError: If the task is already in a terminal state.
        """
        task = self._tasks[task_id]
        happy_path = {
            TaskStatus.PENDING: TaskStatus.REPLICATING,
            TaskStatus.REPLICATING: TaskStatus.TESTING,
            TaskStatus.TESTING: TaskStatus.CUTOVER,
            TaskStatus.CUTOVER: TaskStatus.COMPLETE,
        }
        if task.status not in happy_path:
            raise InvalidTransitionError(
                f"Task {task_id} is in terminal state {task.status.value}"
            )
        return self.transition(task_id, happy_path[task.status], note)

    def summary(self) -> dict[str, int]:
        """Return a count of tasks grouped by status.

        Returns:
            A mapping of status value to the number of tasks in that status.
            Statuses with no tasks are omitted.
        """
        counts: dict[str, int] = {}
        for task in self._tasks.values():
            counts[task.status.value] = counts.get(task.status.value, 0) + 1
        return counts
