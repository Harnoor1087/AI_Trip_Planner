import pytest

from planner.service import PlannerService


def test_start_returns_clarification_without_calling_external_services():
    response = PlannerService().start("I want a relaxing holiday")

    assert response.status == "needs_clarification"
    assert [question.key for question in response.clarification_questions] == [
        "destination",
        "dates",
        "budget",
    ]


def test_clarification_answers_update_the_same_session():
    service = PlannerService()
    initial = service.start("Plan a trip")

    response = service.answer_clarifications(
        initial.session_id,
        {"destination": "Goa", "duration_days": 5},
    )

    assert response.session_id == initial.session_id
    assert response.requirements.destination == "Goa"
    assert response.requirements.duration_days == 5
    assert response.status == "planning"


def test_unknown_session_is_rejected():
    with pytest.raises(KeyError, match="unknown session"):
        PlannerService().answer_clarifications("missing", {"destination": "Goa"})


def test_quick_draft_labels_assumptions():
    response = PlannerService().start("Plan a trip to Goa", quick_draft=True)

    assert response.status == "planning"
    assert response.requirements.duration_days == 3
    assert response.assumptions