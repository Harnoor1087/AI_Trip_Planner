# 🌍 AI Trip Planner

An agentic travel-planning app built with **LangGraph** and **LangChain**. A ReAct-style agent takes a natural-language trip request (e.g. *"Plan a trip to Goa for 5 days"*), reasons over multiple tool calls — weather, places, expenses, and currency conversion — and returns a complete day-by-day itinerary.

The app is split into two services:
- A **FastAPI** backend that hosts the LangGraph agent (`main.py`)
- A **Streamlit** chat UI that calls the backend over HTTP (`streamlit_app.py`)

## How it works

```
User query → Streamlit UI → FastAPI /query endpoint → LangGraph agent
                                                             │
                                        ┌────────────────────┼────────────────────┐
                                        ▼                    ▼                    ▼
                                 Weather tools         Place search tools    Expense / currency tools
                              (OpenWeatherMap)     (Google Places + Tavily)  (ExchangeRate-API, Alpha Vantage)
```

The agent graph (`agent/agentic_workflow.py`) binds all tools to an LLM (Groq or OpenAI) and loops between an `agent` node and a `tools` node until it can answer the query, following `tools_condition` from LangGraph's prebuilt `ToolNode`.

## Features

- 🗺️ Attraction, restaurant, activity, and transportation search (Google Places, with Tavily web search as a fallback)
- ☀️ Current weather and multi-day forecasts (OpenWeatherMap)
- 💰 Expense estimation — hotel costs, total trip cost, and daily budget
- 💱 Currency conversion (ExchangeRate-API, plus an Alpha Vantage-based tool)
- 🔁 Switchable LLM backend: **Groq** (`llama-3.3-70b-versatile`) or **OpenAI** (`o4-mini`), set in `config/config.yaml`
- 📄 Exports the generated plan as a Markdown file (`utils/save_to_document.py`)

## Project structure

```
AI_Trip_Planner/
├── agent/                  # LangGraph agent definition (GraphBuilder)
├── config/                 # config.yaml — LLM provider/model selection
├── exception/               # custom exception handling
├── logger/                  # logging setup
├── notebook/                 # experiments.ipynb — scratch/dev notebook
├── prompt_library/          # system prompt for the agent
├── tools/                    # LangChain @tool wrappers (weather, places, expense, currency)
├── utils/                    # underlying service clients + config/model loaders
├── main.py                   # FastAPI backend, exposes POST /query
├── streamlit_app.py           # Streamlit chat frontend
├── requirements.txt
├── setup.py
└── pyproject.toml
```

## Prerequisites

- Python **3.13** (see `.python-version`; `pyproject.toml` allows >=3.12)
- API keys for the services you plan to use (see below)

## Setup

1. **Clone the repo**
   ```bash
   git clone https://github.com/Harnoor1087/AI_Trip_Planner.git
   cd AI_Trip_Planner
   ```

2. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configure environment variables**

   Create a `.env` file in the project root:
   ```env
   # LLM providers (config/config.yaml defaults to "groq")
   GROQ_API_KEY=your_groq_api_key
   OPENAI_API_KEY=your_openai_api_key

   # Place search
   GPLACES_API_KEY=your_google_places_api_key
   TAVILY_API_KEY=your_tavily_api_key

   # Weather
   OPENWEATHERMAP_API_KEY=your_openweathermap_api_key

   # Currency / expense tools
   EXCHANGE_RATE_API_KEY=your_exchangerate_api_key
   ALPHAVANTAGE_API_KEY=your_alphavantage_api_key
   ```
   `.env` is already covered by `.gitignore`, so it won't be committed.

   > By default the agent uses the **Groq** provider (`GROQ_API_KEY` required). To use OpenAI instead, change `model_provider="groq"` to `model_provider="openai"` in `main.py` and set `OPENAI_API_KEY`.

## Running the app

Run the backend and frontend in two separate terminals (same virtual environment activated in both).

**Terminal 1 — start the FastAPI backend:**
```bash
uvicorn main:app --reload --port 8000
```

**Terminal 2 — start the Streamlit frontend:**
```bash
streamlit run streamlit_app.py
```

Streamlit will open at `http://localhost:8501` and send requests to the backend at `http://localhost:8000/query`.

## API

The planner is clarification-first. Start with `POST /plans`; if required details
are missing, answer the returned questions through the clarification endpoint.

### `POST /plans`

**Request body:**
```json
{
   "question": "Plan a 5 day trip to Goa for two people",
   "quick_draft": false
}
```

The response includes a stable `session_id`, a `status`, validated requirements,
and clarification questions when more information is needed.

### `POST /plans/{session_id}/clarify`

**Request body:**
```json
{
   "answers": {
      "budget": "1200",
      "currency": "USD"
   },
   "quick_draft": false
}
```

Use `/healthz` and `/readyz` for service checks. `POST /query` remains available
as a compatibility endpoint for the original Streamlit client.

### `POST /query`

**Request body:**
```json
{
  "question": "Plan a 5 day trip to Goa"
}
```

**Response:**
```json
{
  "answer": "<full itinerary generated by the agent>"
}
```

Validation errors return HTTP 422 and unknown sessions return HTTP 404. Provider
failures are represented as warnings or degraded results once research execution
is enabled; raw exceptions and credentials are not returned to clients.

## Notes

- The first call to `/query` regenerates `my_graph.png`, a Mermaid visualization of the agent graph, in the project root.
- Generated trip plans can be exported to Markdown via `utils/save_to_document.py`, saved under `./output/`.

## License

No license specified yet — add one if you plan to share or open this project up for contributions.