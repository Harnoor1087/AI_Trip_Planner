from __future__ import annotations

import os

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from domain.models import PlanResponse
from planner.service import PlannerService


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=4_000)
    quick_draft: bool = False


class ClarificationRequest(BaseModel):
    answers: dict[str, str | int] = Field(default_factory=dict)
    quick_draft: bool = False


planner_service = PlannerService()
app = FastAPI(
    title="AI Trip Planner API",
    version="1.0.0",
    description="Clarification-first trip planning with grounded research.",
)

allowed_origins = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOW_ORIGINS", "http://localhost:8501").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type", "X-Request-ID"],
)


@app.get("/healthz")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/readyz")
def readiness_check() -> dict[str, str]:
    return {"status": "ready"}


@app.post("/plans", response_model=PlanResponse, status_code=status.HTTP_200_OK)
def create_plan(request: QueryRequest) -> PlanResponse:
    try:
        return planner_service.start(request.question, quick_draft=request.quick_draft)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post(
    "/plans/{session_id}/clarify",
    response_model=PlanResponse,
    status_code=status.HTTP_200_OK,
)
def clarify_plan(session_id: str, request: ClarificationRequest) -> PlanResponse:
    try:
        return planner_service.answer_clarifications(
            session_id,
            request.answers,
            quick_draft=request.quick_draft,
        )
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/query")
def query_travel_agent(request: QueryRequest) -> dict[str, object]:
    """Compatibility endpoint for the original Streamlit client."""

    response = create_plan(request)
    if response.status == "needs_clarification":
        questions = "\n".join(
            f"- {question.question}" for question in response.clarification_questions
        )
        answer = f"Before I plan this trip, I need a few details:\n{questions}"
    else:
        answer = (
            "Your trip request is ready for planning. "
            "Use the structured /plans response to continue."
        )
    return {"answer": answer, "plan": response.model_dump(mode="json")}