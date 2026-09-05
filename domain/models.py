from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


PlanStatus = Literal["needs_clarification", "planning", "completed", "degraded"]


class TripRequirements(BaseModel):
    """Validated inputs used by the planner and its research tools."""

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)

    destination: str | None = Field(default=None, min_length=2, max_length=160)
    start_date: date | None = None
    end_date: date | None = None
    duration_days: int | None = Field(default=None, ge=1, le=90)
    travelers: int = Field(default=1, ge=1, le=50)
    budget: Decimal | None = Field(default=None, gt=0)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    interests: list[str] = Field(default_factory=list, max_length=12)
    pace: Literal["relaxed", "balanced", "packed"] = "balanced"
    accessibility: str | None = Field(default=None, max_length=500)
    dietary_needs: list[str] = Field(default_factory=list, max_length=12)
    constraints: list[str] = Field(default_factory=list, max_length=20)

    @model_validator(mode="after")
    def validate_dates_and_currency(self) -> "TripRequirements":
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError("end_date must be on or after start_date")
            calculated_days = (self.end_date - self.start_date).days + 1
            if self.duration_days and self.duration_days != calculated_days:
                raise ValueError("duration_days does not match the supplied dates")
        if not self.currency.isalpha():
            raise ValueError("currency must be a three-letter ISO code")
        self.currency = self.currency.upper()
        return self


class ClarificationQuestion(BaseModel):
    key: str
    question: str
    required: bool = True
    choices: list[str] = Field(default_factory=list)


class SourceReference(BaseModel):
    provider: str
    title: str
    url: str | None = None
    fetched_at: str
    confidence: Literal["high", "medium", "low"] = "medium"


class PlanWarning(BaseModel):
    code: str
    message: str
    severity: Literal["info", "warning", "error"] = "warning"


class PlanResponse(BaseModel):
    """Stable response envelope returned by the planner service."""

    plan_id: str
    session_id: str
    status: PlanStatus
    requirements: TripRequirements
    clarification_questions: list[ClarificationQuestion] = Field(default_factory=list)
    answer: str | None = None
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[PlanWarning] = Field(default_factory=list)
    sources: list[SourceReference] = Field(default_factory=list)