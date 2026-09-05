from __future__ import annotations

import re

from domain.models import ClarificationQuestion, TripRequirements


_DURATION_PATTERN = re.compile(r"\b(\d{1,2})\s*(?:day|days|night|nights)\b", re.IGNORECASE)


def extract_initial_requirements(question: str) -> TripRequirements:
    """Extract only high-confidence facts; the agent handles richer parsing."""

    duration_match = _DURATION_PATTERN.search(question)
    duration_days = int(duration_match.group(1)) if duration_match else None
    destination = None
    destination_match = re.search(
        r"\b(?:to|in|visit)\s+([A-Za-z][A-Za-z .'-]{1,80}?)(?=\s+for\s+\d|\s+\d+\s*(?:day|days|night|nights)\b|[,.!?]|$)",
        question,
        re.IGNORECASE,
    )
    if destination_match:
        destination = destination_match.group(1).strip(" .,!?-")
    return TripRequirements(destination=destination, duration_days=duration_days)


def missing_requirements(requirements: TripRequirements) -> list[ClarificationQuestion]:
    """Return a stable, prioritized list of information needed to research a trip."""

    questions: list[ClarificationQuestion] = []
    if not requirements.destination:
        questions.append(
            ClarificationQuestion(key="destination", question="Where would you like to travel?")
        )
    if not requirements.duration_days and not (
        requirements.start_date and requirements.end_date
    ):
        questions.append(
            ClarificationQuestion(
                key="dates",
                question="What dates or trip length should I plan for?",
            )
        )
    if not requirements.budget:
        questions.append(
            ClarificationQuestion(
                key="budget",
                question="What is your approximate total budget and preferred currency?",
                required=False,
            )
        )
    return questions