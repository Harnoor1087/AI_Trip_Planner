from datetime import date
from decimal import Decimal

import pytest
from pydantic import ValidationError

from domain.clarification import extract_initial_requirements, missing_requirements
from domain.models import TripRequirements


def test_extracts_destination_and_duration():
    requirements = extract_initial_requirements("Plan a trip to Goa for 5 days")

    assert requirements.destination == "Goa"
    assert requirements.duration_days == 5
    assert missing_requirements(requirements)[0].key == "budget"


def test_missing_core_requirements_are_prioritized():
    questions = missing_requirements(TripRequirements())

    assert [question.key for question in questions] == ["destination", "dates", "budget"]


def test_rejects_inconsistent_dates_and_duration():
    with pytest.raises(ValidationError, match="duration_days"):
        TripRequirements(
            start_date=date(2026, 9, 5),
            end_date=date(2026, 9, 7),
            duration_days=5,
        )


def test_normalizes_currency_and_validates_budget():
    requirements = TripRequirements(currency="eur", budget=Decimal("1200"))

    assert requirements.currency == "EUR"

    with pytest.raises(ValidationError):
        TripRequirements(budget=0)