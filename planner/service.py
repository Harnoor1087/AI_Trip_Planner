from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from uuid import uuid4

from domain.clarification import extract_initial_requirements, missing_requirements
from domain.models import PlanResponse, TripRequirements


@dataclass
class PlanningSession:
    session_id: str
    requirements: TripRequirements
    question: str
    plan_id: str = field(default_factory=lambda: str(uuid4()))


class InMemorySessionStore:
    """Small local store; replaceable by a persistent checkpointer in deployment."""

    def __init__(self) -> None:
        self._sessions: dict[str, PlanningSession] = {}

    def save(self, session: PlanningSession) -> None:
        self._sessions[session.session_id] = session

    def get(self, session_id: str) -> PlanningSession | None:
        return self._sessions.get(session_id)


class PlannerService:
    def __init__(self, session_store: InMemorySessionStore | None = None) -> None:
        self.sessions = session_store or InMemorySessionStore()

    def start(self, question: str, *, quick_draft: bool = False) -> PlanResponse:
        normalized_question = question.strip()
        if not normalized_question:
            raise ValueError("question must not be empty")

        requirements = extract_initial_requirements(normalized_question)
        session = PlanningSession(
            session_id=str(uuid4()),
            requirements=requirements,
            question=normalized_question,
        )
        self.sessions.save(session)
        return self._response(session, quick_draft=quick_draft)

    def answer_clarifications(
        self,
        session_id: str,
        answers: dict[str, str | int | date],
        *,
        quick_draft: bool = False,
    ) -> PlanResponse:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(f"unknown session: {session_id}")

        updates = self._coerce_answers(answers)
        session.requirements = session.requirements.model_copy(update=updates)
        self.sessions.save(session)
        return self._response(session, quick_draft=quick_draft)

    def _response(self, session: PlanningSession, *, quick_draft: bool) -> PlanResponse:
        questions = missing_requirements(session.requirements)
        required_questions = [question for question in questions if question.required]
        if required_questions and not quick_draft:
            return PlanResponse(
                plan_id=session.plan_id,
                session_id=session.session_id,
                status="needs_clarification",
                requirements=session.requirements,
                clarification_questions=questions,
            )

        assumptions = []
        if quick_draft:
            if not session.requirements.duration_days:
                session.requirements.duration_days = 3
                assumptions.append("A three-day duration was assumed for this quick draft.")
            if not session.requirements.budget:
                assumptions.append("No budget was supplied; costs will be presented as estimates.")
        return PlanResponse(
            plan_id=session.plan_id,
            session_id=session.session_id,
            status="planning",
            requirements=session.requirements,
            assumptions=assumptions,
        )

    @staticmethod
    def _coerce_answers(answers: dict[str, str | int | date]) -> dict[str, object]:
        updates: dict[str, object] = {}
        if "destination" in answers:
            updates["destination"] = str(answers["destination"]).strip()
        if "duration_days" in answers:
            updates["duration_days"] = int(answers["duration_days"])
        if "budget" in answers:
            updates["budget"] = answers["budget"]
        if "currency" in answers:
            updates["currency"] = str(answers["currency"]).upper()
        return updates