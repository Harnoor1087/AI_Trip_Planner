from __future__ import annotations

import os

import requests
import streamlit as st


BASE_URL = os.getenv("TRIP_PLANNER_API_URL", "http://localhost:8000").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("TRIP_PLANNER_REQUEST_TIMEOUT", "30"))

st.set_page_config(
    page_title="AI Trip Planner",
    page_icon="🌍",
    layout="centered",
    initial_sidebar_state="expanded",
)

st.title("AI Trip Planner")
st.caption("Build a trip plan from live research, explicit assumptions, and your constraints.")

if "plan" not in st.session_state:
    st.session_state.plan = None


def submit_plan(question: str, quick_draft: bool) -> None:
    try:
        response = requests.post(
            f"{BASE_URL}/plans",
            json={"question": question, "quick_draft": quick_draft},
            timeout=REQUEST_TIMEOUT,
        )
        response.raise_for_status()
        st.session_state.plan = response.json()
    except requests.RequestException as error:
        st.error(f"The planning service is unavailable: {error}")


with st.form("trip_request"):
    question = st.text_area(
        "Describe your trip",
        placeholder="Plan a 5 day trip to Goa for two people who enjoy beaches and local food.",
        height=100,
    )
    quick_draft = st.checkbox(
        "Create a quick draft when details are missing",
        help="The draft will label every assumption it makes.",
    )
    submitted = st.form_submit_button("Start planning", type="primary")

if submitted:
    if question.strip():
        with st.spinner("Checking what I need to plan this well..."):
            submit_plan(question, quick_draft)
    else:
        st.warning("Describe the destination and trip you have in mind.")


plan = st.session_state.plan
if plan:
    if plan["status"] == "needs_clarification":
        st.subheader("A few details will improve the plan")
        with st.form("clarifications"):
            answers: dict[str, str | int] = {}
            for item in plan["clarification_questions"]:
                answer = st.text_input(item["question"], key=f"answer_{item['key']}")
                if answer.strip():
                    answers[item["key"]] = answer.strip()
            submitted_answers = st.form_submit_button("Continue")

        if submitted_answers:
            try:
                response = requests.post(
                    f"{BASE_URL}/plans/{plan['session_id']}/clarify",
                    json={"answers": answers, "quick_draft": quick_draft},
                    timeout=REQUEST_TIMEOUT,
                )
                response.raise_for_status()
                st.session_state.plan = response.json()
                st.rerun()
            except requests.RequestException as error:
                st.error(f"The planning service is unavailable: {error}")
    else:
        st.subheader("Planning started")
        for assumption in plan.get("assumptions", []):
            st.info(assumption)
        st.write("The structured planner has accepted your requirements and is ready for research.")

    warnings = plan.get("warnings", [])
    for warning in warnings:
        st.warning(warning["message"])