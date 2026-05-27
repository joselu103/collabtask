# src/tasks/state_machine.py
from src.tasks.models import TaskStatus as TS


class InvalidTransitionError(Exception): ...


ALLOWED_TRANSITIONS = {
    TS.BACKLOG: [TS.IN_PROGRESS, TS.CANCELLED],
    TS.IN_PROGRESS: [TS.IN_REVIEW, TS.CANCELLED],
    TS.IN_REVIEW: [TS.DONE, TS.IN_PROGRESS, TS.CANCELLED],
    TS.DONE: [],
    TS.CANCELLED: [],
}


def validate_transition(current_status: TS, next_status: TS) -> None:
    """Ensure the task status transition is allowed.

    Raises:
        InvalidTransitionError: if the transition is not valid.
    """
    if next_status not in ALLOWED_TRANSITIONS[current_status]:
        raise InvalidTransitionError(f"{current_status} -> {next_status}")
