# tests/unit/test_task_service.py
import pytest

from src.tasks.models import TaskStatus
from src.tasks.state_machine import (
    ALLOWED_TRANSITIONS,
    InvalidTransitionError,
    validate_transition,
)


def test_ensure_all_status_in_allowed_transitions():
    for status in TaskStatus:
        assert status in ALLOWED_TRANSITIONS.keys()


VALID_TRANSITIONS = [
    (current, next_)
    for current, allowed in ALLOWED_TRANSITIONS.items()
    for next_ in allowed
]

INVALID_TRANSITIONS = [
    (current, next_)
    for current in TaskStatus
    for next_ in TaskStatus
    if next_ not in ALLOWED_TRANSITIONS[current]
]


@pytest.mark.parametrize(
    ("current_status", "next_status"),
    VALID_TRANSITIONS,
)
def test_valid_transitions(
    current_status: TaskStatus,
    next_status: TaskStatus,
) -> None:
    validate_transition(current_status, next_status)


@pytest.mark.parametrize(
    ("current_status", "next_status"),
    INVALID_TRANSITIONS,
)
def test_invalid_transitions(
    current_status: TaskStatus,
    next_status: TaskStatus,
) -> None:
    with pytest.raises(InvalidTransitionError):
        validate_transition(current_status, next_status)
