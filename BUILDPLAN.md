# Fleet Ops Co-Pilot — Daily Build Plan (Days 1–21)

## Project
Multi-agent fleet operations assistant. LangGraph + OpenAI Agents SDK, DuckDB, FastAPI, Next.js streaming UI.

## Stack
- Python 3.12+, LangGraph, OpenAI SDK, DuckDB, FastAPI, httpx, Pydantic v2
- Conventions: `X | None` never `Optional`, `list[X]` never `List`, no `dict[str, Any]`, no `requests`
- truststore for system CA trust on all HTTPS clients

## Tasks

### DAY 1
**Task:** Project scaffolding.
Create `pyproject.toml` (project name `fleet-ops-copilot`, Python `>=3.12`, dependencies: `langraph`, `openai`, `duckdb`, `fastapi`, `uvicorn`, `httpx`, `pydantic`, `truststore`, `faker`, `python-dotenv`). Create directory structure: `fleet_ops/`, `fleet_ops/tools/`, `fleet_ops/agents/`, `fleet_ops/data/`, `fleet_ops/api/`, `tests/`, `evals/`. Create `.gitignore` (venv, .env, __pycache__, *.pyc, data/csv/, data/db/). Create `.env.example` with `OPENAI_API_KEY=`, `LANGFUSE_PUBLIC_KEY=`, `LANGFUSE_SECRET_KEY=`, `LANGFUSE_HOST=`. Create `fleet_ops/__init__.py`. Do NOT create README yet.
**Commit message:** `feat: project scaffolding — pyproject.toml, directory structure, gitignore`

### DAY 2
**Task:** Synthetic vehicle data.
Create `fleet_ops/data/generate.py`. Use Faker to generate 500 vehicles as a list of Pydantic models (`Vehicle`: id, vin, make, model, year, license_plate, state, fuel_type, odometer_miles, status). Write to `data/csv/vehicles.csv`. Add a `__main__` block. Seed random with 42 for reproducibility. Use `list[Vehicle]` not `List[Vehicle]`. No Optional — use `str | None`.
**Commit message:** `feat: synthetic vehicle data generator — 500 vehicles via Faker`

### DAY 3
**Task:** Synthetic driver data.
In `fleet_ops/data/generate.py` add driver generation. `Driver` Pydantic model: id, name, license_number, license_state, hire_date, safety_score (float 0-100), violations_90d (int), phone, email. Generate 50 drivers, write to `data/csv/drivers.csv`. Assign each vehicle a primary `driver_id` from the 50 drivers (update vehicles.csv). Re-run full generation from scratch each time.
**Commit message:** `feat: synthetic driver data — 50 drivers with safety scores`

### DAY 4
**Task:** Synthetic trip data.
Add trip generation to `generate.py`. `Trip` Pydantic model: id, vehicle_id, driver_id, start_time (ISO8601), end_time, distance_miles (float), fuel_used_gallons (float), start_lat, start_lon, end_lat, end_lon, max_speed_mph (int), avg_speed_mph (int). Generate 30 days of trips (2026-04-01 to 2026-04-30), 3-8 trips per vehicle per day, write to `data/csv/trips.csv`.
**Commit message:** `feat: synthetic trip data — 30 days, 500 vehicles`

### DAY 5
**Task:** Synthetic alert data.
Add alert generation. `Alert` Pydantic model: id, trip_id, vehicle_id, driver_id, alert_type (enum: SPEEDING, HARSH_BRAKING, HARSH_ACCELERATION, IDLING, SEATBELT), severity (enum: LOW, MEDIUM, HIGH), timestamp, speed_mph (int | None), description. Generate alerts proportional to driver safety score (low score = more alerts). Write to `data/csv/alerts.csv`. Include at least 2000 alerts total.
**Commit message:** `feat: synthetic alert data — speeding, harsh events, idling alerts`

### DAY 6
**Task:** DuckDB data layer.
Create `fleet_ops/storage/db.py`. `FleetDatabase` class: `__init__(db_path: str)`, `initialize()` method that creates tables and ingests CSVs from `data/csv/` using DuckDB's native CSV reader. Methods: `execute(sql: str, params: list | None = None) -> list[dict]`. Create `fleet_ops/storage/__init__.py`. Add `data/db/` to gitignore. Write a smoke-test script `scripts/init_db.py` that initializes the DB and prints row counts.
**Commit message:** `feat: DuckDB storage layer — schema, CSV ingest, query interface`

### DAY 7
**Task:** Tools — get_vehicle and list_alerts.
Create `fleet_ops/tools/fleet_tools.py`. Implement two async tool functions using `FleetDatabase`. `get_vehicle(vehicle_id: str) -> VehicleResult | None` — fetches vehicle + current driver info. `list_alerts(start: str, end: str, vehicle_id: str | None = None) -> list[AlertResult]` — filters alerts by date range. All return types are Pydantic models. Create `fleet_ops/tools/__init__.py`. Use httpx only if external calls needed (not here).
**Commit message:** `feat: fleet tools — get_vehicle, list_alerts with Pydantic responses`

### DAY 8
**Task:** Tools — get_driver_score and query_trips_sql.
In `fleet_ops/tools/fleet_tools.py` add: `get_driver_score(driver_id: str) -> DriverScoreResult | None` — returns driver info + calculated safety metrics (trips_count, alerts_count, avg_speed). `query_trips_sql(sql: str) -> list[dict]` — executes arbitrary read-only SQL against DuckDB (validate it's SELECT only, raise ValueError otherwise). All Pydantic models.
**Commit message:** `feat: fleet tools — get_driver_score, query_trips_sql (read-only SQL guard)`

### DAY 9
**Task:** Tool schemas and registry.
Create `fleet_ops/tools/registry.py`. Define all 4 tools as OpenAI function-calling schema dicts (`name`, `description`, `parameters` with JSON Schema). Create `TOOL_REGISTRY: dict[str, callable]` mapping tool name to async function. Create `fleet_ops/tools/models.py` with all Pydantic response models consolidated. Add `fleet_ops/core/__init__.py` and `fleet_ops/core/config.py` loading env vars with `python-dotenv`.
**Commit message:** `feat: tool registry and Pydantic response models consolidated`

### DAY 10
**Task:** LangGraph single-agent — state schema and graph skeleton.
Create `fleet_ops/agents/state.py`: `AgentState` TypedDict with `messages: list`, `tool_calls_made: list[str]`, `final_answer: str | None`. Create `fleet_ops/agents/single_agent.py`: build a LangGraph `StateGraph` with nodes `call_model` and `call_tools`. Wire edges: START → call_model → (tools if tool_calls else END). Return compiled graph.
**Commit message:** `feat: LangGraph single-agent graph — state schema, model/tool nodes`

### DAY 11
**Task:** LangGraph single-agent — complete loop.
Flesh out `call_model` node (calls OpenAI with tool schemas) and `call_tools` node (executes tools from registry, handles parallel calls with `asyncio.gather`). Add `run_agent(query: str) -> str` async function. Write `scripts/test_agent.py` that runs the demo query: "Find vehicles with speeding events in the last 7 days". Verify it fans out parallel tool calls.
**Commit message:** `feat: LangGraph single-agent loop complete — parallel tool execution`

### DAY 12
**Task:** Multi-agent — planner.
Create `fleet_ops/agents/planner.py`. `PlannerAgent`: takes user query, returns a structured `ExecutionPlan` Pydantic model with `steps: list[PlanStep]` where each step has `tool_name`, `tool_args`, `depends_on: list[int]`. System prompt focuses on decomposing fleet queries into parallel tool calls where possible. Use OpenAI structured output mode.
**Commit message:** `feat: planner agent — structured execution plan with dependency graph`

### DAY 13
**Task:** Multi-agent — executor with parallel fan-out.
Create `fleet_ops/agents/executor.py`. `ExecutorAgent`: takes `ExecutionPlan`, groups independent steps (no `depends_on`), executes each group with `asyncio.gather`. Returns `ExecutionResult` with per-step results and timing. Wire into LangGraph as `executor` node after `planner` node.
**Commit message:** `feat: executor agent — parallel tool fan-out with asyncio.gather`

### DAY 14
**Task:** Multi-agent — critic and final synthesis.
Create `fleet_ops/agents/critic.py`. `CriticAgent`: reviews `ExecutionResult`, checks for missing data or low-confidence results, can request one retry pass. Create `fleet_ops/agents/synthesizer.py`: formats final natural language answer. Wire full graph: planner → executor → critic → (retry executor | synthesizer). Write `scripts/test_multi_agent.py`.
**Commit message:** `feat: critic agent and synthesizer — full planner/executor/critic graph`

### DAY 15
**Task:** Eval dataset part 1.
Create `evals/dataset.yaml`. Write 15 eval cases. Each case: `id`, `query`, `expected_tools: list[str]`, `expected_answer_contains: list[str]`, `requires_parallel: bool`, `category` (fleet_status | driver_safety | trip_analysis | alert_lookup). Cover the demo query + 14 varied cases. Format: YAML list.
**Commit message:** `feat: eval dataset — first 15 cases covering all query categories`

### DAY 16
**Task:** Eval dataset part 2 + substring scorer.
Add 15 more eval cases to `evals/dataset.yaml` (total 30). Create `evals/scorers/substring_scorer.py`: checks `expected_answer_contains` strings are in the final answer (case-insensitive). `SubstringScorer` class with `score(case, result) -> ScorerResult` returning pass/fail + details. Create `evals/scorers/__init__.py` and `evals/models.py` with Pydantic models for cases and results.
**Commit message:** `feat: eval dataset complete (30 cases) + substring scorer`

### DAY 17
**Task:** LLM-judge and tool-routing scorers.
Create `evals/scorers/llm_judge.py`: calls OpenAI to judge answer quality on 0-1 scale, prompt asks "Does this answer correctly address the query given the context?". Create `evals/scorers/tool_routing.py`: checks that `expected_tools` were actually called during execution (compare against `tool_calls_made` in state). Both return `ScorerResult`.
**Commit message:** `feat: LLM-judge scorer and tool-routing scorer`

### DAY 18
**Task:** Parallel-execution scorer + eval runner.
Create `evals/scorers/parallel_scorer.py`: for cases where `requires_parallel=true`, checks that the executor used `asyncio.gather` on ≥2 tools (inspect timing: parallel calls finish within 500ms of each other). Create `evals/runner.py`: loads `dataset.yaml`, runs agent on each case, applies all scorers, writes `evals/results.json`. Print per-case pass/fail table.
**Commit message:** `feat: parallel-execution scorer + eval runner with JSON output`

### DAY 19
**Task:** FastAPI service.
Create `fleet_ops/api/app.py`. Endpoints: `POST /query` (body: `QueryRequest`, response: `QueryResponse` with `answer`, `tool_calls`, `latency_ms`, `trace_id`), `GET /health`. Use `lifespan` context manager to init DB. All request/response types are Pydantic models. Run with `uvicorn`. Add `scripts/run_api.py`.
**Commit message:** `feat: FastAPI service — /query and /health endpoints`

### DAY 20
**Task:** Langfuse tracing.
Integrate Langfuse into the multi-agent graph. Wrap each agent node (planner, executor, critic, synthesizer) with a Langfuse span. Record: input, output, model, token usage, latency. Add `LANGFUSE_*` env vars to `.env.example`. Add `fleet_ops/observability/tracing.py` with a `get_tracer()` function. Update FastAPI to include `trace_id` in response. Take a screenshot of a trace (save description in README later).
**Commit message:** `feat: Langfuse tracing — spans on all agent nodes, trace_id in API response`

### DAY 21
**Task:** EVALS.md, Fly.io config, final polish.
Create `EVALS.md` with table: scorer | pass_rate | avg_latency_ms | notes. Populate with actual eval run results. Create `fly.toml` for Fly.io deployment (app name `fleet-ops-copilot`, region `lax`, port 8000). Create `Dockerfile` (python:3.12-slim, install deps, run uvicorn). Create `scripts/run_evals.sh`. Do NOT create README (will be done in Week 8 polish).
**Commit message:** `feat: EVALS.md scorecard, Fly.io config, Dockerfile`
