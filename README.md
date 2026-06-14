# Multi Agent Demo, Coding Challenge
## Executive Summary
- This solution implements a lightweight full-stack agent system with a modular and extensible architecture with maintainability, clean API design, and extensibility
- The backend follows a clear separation of concerns, with an Agent Controller responsible for request interpretation, tool selection, execution orchestration, and trace generation. 
- Tool functionality is abstracted through a common interface, allowing new tools to be added with minimal changes. 
- The system includes comprehensive error handling, structured execution tracing, and persistent task storage to ensure transparency and reliability. 
- End-to-end local development mirrors a complete engineering lifecycle: design (layered architecture and API design), build (React frontend + Python backend with typed schemas and modular agent/tool packages), test (37 backend tests across unit, integration, API, and E2E plus frontend), run (local dual-process or Docker Compose with nginx + Uvicorn + persisted SQLite), and operate (health checks, admin analytics, audit logs, cost dashboards).


---


## Run locally

### Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # optional — defaults work for local dev
python -m app.main
```

API: **http://localhost:8000** · Docs: **http://localhost:8000/api/docs**

### Frontend

```bash
cd frontend
npm install
npm run dev
```

UI: **http://localhost:5173** (Vite proxies `/api` → `localhost:8000`)

### Both with Docker

From project root (`devbuildJB/`):

```bash
# Production images (nginx + uvicorn, persisted DB volume)
docker compose up --build

# Dev hot reload
docker compose -f docker-compose.dev.yml up --build
```

| URL | Service |
|-----|---------|
| http://localhost:5173 | Web UI |
| http://localhost:8000 | API + `/api/docs` |

```bash
docker compose down          # stop
docker compose down -v       # stop + wipe DB volume
```

Optional: `cp docker/.env.example .env` and set `SECRET_KEY`.

**Default logins:** `admin` / `admin1234` (admin) · `user` / `user1234` · `test1` / `test1` (5-task quota)

---
## Screenshots
Front page: 
<img width="1908" height="1014" alt="Screenshot 2026-06-14 at 6 49 17 PM" src="https://github.com/user-attachments/assets/0cc73016-4cbf-46df-a8f3-b7c6abc4c943" />
<img width="922" height="759" alt="Screenshot 2026-06-14 at 6 49 33 PM" src="https://github.com/user-attachments/assets/3480f468-e2e2-4cc8-aec6-37d36bfe1725" />
<img width="1663" height="958" alt="Screenshot 2026-06-14 at 6 49 51 PM" src="https://github.com/user-attachments/assets/0b362055-16a9-4f22-8165-179ca099b2b8" />
<img width="1141" height="875" alt="Screenshot 2026-06-14 at 6 49 58 PM" src="https://github.com/user-attachments/assets/8e8aab4c-d2f0-4fbe-980c-3b3cdf60eb5d" />
<img width="1087" height="955" alt="Screenshot 2026-06-14 at 6 50 08 PM" src="https://github.com/user-attachments/assets/84b1dccd-8faf-46d1-8a4c-6e91f81e6e27" />

## Dependencies

| Layer | Requirements |
|-------|----------------|
| **Runtime** | Python 3.11+, Node.js 18+, npm |
| **Docker** | Docker Engine 24+ with Compose v2 |
| **Backend** | FastAPI, Uvicorn, SQLAlchemy 2, aiosqlite, Pydantic, python-jose, passlib/bcrypt, SlowAPI |
| **Frontend** | React 18, TypeScript, Vite 6, MUI 6, Axios, Zustand, Framer Motion |
| **Tests** | pytest, pytest-asyncio, httpx (backend); Vitest (frontend) |

Full pins: `backend/requirements.txt`, `frontend/package.json`.

---

## Assumptions & tradeoffs

Built for **local system deployment** (run on a laptop or `docker compose up`) within a ~12-hour build window. The architecture demonstrates layered agent design, governance, and observability — not production scale.

### Assumptions

- **Single-machine** — One Uvicorn process and one SQLite file on the same host. No load balancer, no worker pool, no external message broker.
- **Localhost-only traffic** — Frontend on `:5173`, API on `:8000`. CORS is locked to `localhost` / `127.0.0.1`
- **No cloud or paid APIs** — No Azure, no LLM API keys, no real weather/billing services. Everything works offline.
- **Seeded demo users** — `admin`, `user`, and `test1` accounts are created at startup (`ensure_default_user`)
- **Short, English task text** — Inputs capped at 5,000 characters. Users express intent in plain English with tool-triggering keywords (e.g. “calculate”, “weather in Tokyo”).
- **Fast, synchronous tools** — All six tools run in-process and return in milliseconds. No long-running jobs, file uploads, or network calls to third parties.
- **Demo audience needs visible agent behavior** — Reviewers should see step-by-step traces, retry recovery, and admin metrics without configuring external observability stacks.
- **HTTPS optional for local dev(secret management)** — JWT travels over HTTP on localhost. `SECRET_KEY` defaults to a dev value, production secret management is out of scope.

### Tradeoffs (what I did and why)

- **Keyword confidence scoring instead of an LLM** — Each tool declares `keywords`; `Tool.confidence()` scores by substring matches (`0.55 + 0.22` per hit, threshold `0.15`). `ToolSelector` picks the highest score. *Why:* no LLM used. *Cost:* no semantic understanding; ambiguous prompts like “help me with numbers and text” may pick the wrong tool unless the user switches to smart-multi mode with 2–3 explicit lines.

- **SQLite file DB with startup `create_all`, not PostgreSQL + Alembic** — Database is `sqlite+aiosqlite:///./storage.db` tables are created on app boot. Docker mounts a named volume at `/app/data`. *Why:* zero database server setup — clone, run, done. *Cost:* single writer; concurrent task submits queue on one file lock; no replication, no connection pooling across instances.

- **Task runs inside the HTTP request, not a background worker** — Both `POST /tasks` and `POST /tasks/stream` create the task row, then `AgentController` runs the full pipeline (`TaskRunner` → workflow → tool) before the response completes. No Celery, Redis, or Temporal. *Why:*  no extra containers for a demo. 

- **220 ms artificial delay on SSE steps only** — `STREAM_STEP_DELAY_SEC = 0.22` is applied when streaming so each trace step is visible in the UI; the sync `POST /tasks` path uses `stream_delay=0`. *Why:* without pacing, steps flash by too fast to demo the execution timeline. *Cost:* streaming is deliberately slower than necessary; not representative of real latency.

- **JWT in Zustand `persist` (localStorage key `bmo-auth`)** — Token, username, and role survive page refresh. Axios attaches `Authorization: Bearer`. *Why:* SPA and API run on different ports locally, avoids cookie domain issues and a BFF layer.

- **Regex-based injection and PII gates, mirrored on frontend** — Backend blocks 11 injection patterns (`ignore previous instructions`, `drop table`, etc.) and 5 PII patterns (email, phone, SSN, SIN) before execution; `securityUtils.ts` mirrors checks for instant UI feedback. Events go to `security_events` and `audit_logs`. *Why:* demonstrates a governance layer without Microsoft Purview or ML classifiers. 

- **Mock tools with scripted failure to show retry demo** — `WeatherMockTool` raises `TransientToolError` on attempt 1 so `RetryExecutor` (max 2 attempts, 0.5 s backoff) produces visible retry steps in the trace. Other tools are pure Python (calculator, text transform, JSON parse). *Why:* shows resilience UX without flaky external APIs or API keys.

- **Cost model is basic, not cloud billing** — `CostTracker` assigns flat USD values per tool call and per “infra line item” (SQLite, FastAPI, Vite); stored in `CostRecord` for the admin dashboard. *Why:* cost observability demo without Azure Cost Management integration. *Cost:* numbers are illustrative, not tied to actual CPU/memory usage.

- **In-process `DistributedTracer` with five named layers** — Tracer records API Gateway → Orchestrator → Agent → Tool → Response timings inside the same Python process. *Why:* shows the observability model from the architecture diagram without OpenTelemetry collectors or App Insights.

- **Admin-only full execution trace** — `_to_task_response` strips `execution_steps` for non-admin users. Admins see full step detail in history. *Why:*  RBAC demo  without a separate audit store.

- **Singleton `ToolRegistry` with six in-process tools** — Tools register at import via a `Tool` ABC; no plugin loading, no separate tool microservices, no sandbox. *Why:* meets the “extensible tool registry” requirement with minimal boilerplate.

- **Docker Compose: nginx + uvicorn, no DB container** — Production compose builds frontend (nginx on `:5173`) and backend (uvicorn on `:8000`); nginx proxies `/api/` with `proxy_buffering off` and 3600 s read timeout for SSE. SQLite lives in a Docker volume on the backend container. *Why:* one command for evaluators who do not want to install Python. 

- **Per-user quota hardcoded for `test1` only** — `quota_service.py` limits `test1` to 5 total task submissions (429 when exceeded); other users have no quota. *Why:* demonstrates access control and quota UX without a billing system. \

This repo is a **reference implementation** for layered agent architecture, governance, and observability — not a production deployment.

---

## Time spent

Approximate effort across the software development lifecycle (~**12 hours** total):

| Phase | Activity | Hours |
|-------|----------|-------|
| **Architecture** | Solution architecture — layered system design and draw.io diagrams (API gateway, agent pipeline, tools, persistence, observability) | 2.0 |
| **Planning** | Implementation planning — module breakdown, API contracts, tool interfaces, trace model | 0.5 |
| **Requirements & design** | Challenge requirements mapping, data models, agent workflow design, UI wireframes | 1.5 |
| **Development (backend)** | FastAPI routes, `AgentController`, tool registry, six tools, SQLite persistence, auth, security gates | 2.5 |
| **Development (frontend)** | React UI — task submit, SSE streaming, execution trace, history, admin pages | 2.5 |
| **Testing** | Backend pytest (unit, integration, API, E2E) and frontend Vitest; manual smoke tests | 2.0 |
| **Documentation** | README, ARCHITECTURE, FEATURES_CHECKLIST, OpenAPI | 1.0 |
| **Deployment** | Docker Compose, nginx config, dev/prod compose files, setup scripts | 0.5 |
| | **Total** | **12.0** |

---

## Anything you would improve with more time: Yes following are the areas I will improve and operate on given I have more time

### Intelligence & agents
- [ ] Replace keyword routing with an **actual LLM** (Azure OpenAI / GPT-4o) based multi-agent orchestrator framework for intent, tool selection, and multi-step planning
- [ ] Tool-calling schema (JSON mode / function calling) with guardrails and output validation
- [ ] Human-in-the-loop for high-risk actions; prompt/version management

### Azure cloud (active-active, 99.9% RTO, 0 RPO)
- [ ] **Azure Container Apps** or **AKS** for API + worker tiers, **Azure Static Web Apps** or Front Door + blob for frontend
- [ ] **Azure Database for PostgreSQL** (Flexible Server) with **geo-redundant backup** and **read replicas** in paired region
- [ ] **Active-active**: multi-region Front Door to regional API pools; **async replication** or CRDB-style DB for **0 RPO** (PostgreSQL sync replica + automatic failover, or Cosmos DB with multi-write)
- [ ] **99.9% RTO**: health probes, auto-scaling, circuit breakers, runbooks; target &lt;8.76 h downtime/year
- [ ] **Azure Cache for Redis** for sessions/rate limits; **Service Bus** or Event Hubs for async task queue if workloads grow

### Secrets & configuration
- [ ] **Azure Key Vault** for `SECRET_KEY`, DB credentials, LLM API keys—no secrets in env files or images
- [ ] Managed identities for app to Key Vault / DB, set rotation policies

### Compliance & governance
- [ ] **Microsoft Purview** / custom DLP for PII, audit log export to **Log Analytics** + immutable **Storage** (WORM)
- [ ] GDPR, data export/delete APIs, retention TTL jobs, residency controls (Canada Central/East)
- [ ] SOC2-aligned controls: access reviews, encryption at rest (TLS 1.2+, CMK), vulnerability scanning

### CI/CD & quality
- [ ] **GitHub Actions** or **Azure DevOps**: lint, `pytest` (unit/integration/API/E2E), Vitest, SAST (Bandit, npm audit), container scan (Trivy)
- [ ] Staged deploy: dev → staging → prod with smoke tests and rollback
- [ ] Contract tests on OpenAPI; load tests (k6) on `/tasks` and `/tasks/stream`

### Infrastructure as code
- [ ] **Terraform** modules: networking (VNet, NSG), AKS/ACA, PostgreSQL, Key Vault, Front Door, Monitor, RBAC
- [ ] Environment separation via workspaces; policy-as-code (Azure Policy)

### Observability & operations
- [ ] **Azure Monitor** + **Application Insights** + OpenTelemetry traces (replace in-process tracer for prod)
- [ ] Alerting on error rate, latency, queue depth, DB replication lag
- [ ] SLO dashboards aligned to 99.9% availability

### Application hardening
- [ ] Migrate SQLite → PostgreSQL, connection pooling; migrations 
- [ ] httpOnly secure cookies or BFF pattern; refresh tokens; optional Entra ID SSO
- [ ] WAF on Front Door; API Management for throttling and API keys
- [ ] Replace mock tools with real APIs (weather, etc.) behind private endpoints

---

## Tests in this demo

```bash
cd backend && bash scripts/run_tests.sh    # unit · integration · API · E2E
cd frontend && npm test                    # Vitest
```

---


## Tech stack used in this demo

| Tier | Stack |
|------|-------|
| **Frontend** | React 18, TypeScript, Vite, MUI, Zustand, Axios, React Router |
| **Backend** | Python 3.11+, FastAPI, Uvicorn, Pydantic |
| **Database** | SQLite, SQLAlchemy 2 (async), aiosqlite |
| **Auth & security** | JWT (python-jose), bcrypt, SlowAPI rate limiting |
| **Streaming** | Server-Sent Events (SSE) for live agent steps |
| **Deploy** | Docker, nginx, Docker Compose |
| **Tests** | pytest (backend), Vitest (frontend) |

---

## Implementation overview of this demo

### Backend

- **API layer** — FastAPI routes under `/api/v1`: task submit (`POST /tasks`, `POST /tasks/stream`), history, auth, tools list, admin metrics. OpenAPI at `/api/docs`.
- **Agent controller** — `AgentController` receives a task, runs the agent pipeline, persists results, and returns output + execution trace.
- **Agent pipeline** — `TaskRunner` parses the request (`TaskAnalyzer`), picks a workflow (`WorkflowDispatcher`), selects a tool via keyword confidence scoring (`ToolSelector` + `ToolRegistry`), executes with retry on transient failures, and emits a structured step trace.
- **Tools** — Six tools behind a `Tool` ABC: TextProcessor, Calculator, WeatherMock (required three + DateTime, JSON, UnitConverter). Registered in a singleton `ToolRegistry`.
- **Persistence** — SQLite stores tasks, execution steps, tool usage, users, audit logs, and security events.
- **Security** — JWT login/register, role-based access (admin/user), prompt-injection and PII blocking before execution, per-user quotas.

**Request flow:** Client → API validation → `AgentController` → `TaskRunner` → tool execution → trace + result saved to SQLite → response/SSE stream.

### Frontend

- **SPA shell** — React + React Router: Home (task submit), History, Admin analytics, dashboard, and cost tracking. Login gate with JWT persisted in Zustand.
- **Task submission** — `TaskInput` supports single-task and multi-tool (smart routing) modes. Submits via SSE (`POST /tasks/stream`) and shows live step updates during execution.
- **Results & trace** — `TaskResult` displays status and output. `ExecutionTrace` shows a timeline of agent steps (input → analyze → tool selection → execution → output). Admin sees full trace; regular users see results and step progress.
- **History** — `TaskHistory` lists past tasks with pagination, search, and expandable detail (admin can inspect full trace per task).
- **Admin UI** — Metrics dashboard (success rates, tool usage, audit logs), user/task management, and mock cost tracking.
- **Client validation** — Mirrors backend injection and PII checks before submit.

**Request flow:** User input → client validation → SSE stream to backend → live step events → final task result displayed.

---

## Project structure

```
devbuildJB/
├── backend/          # FastAPI app (app/agents, tools, persistence)
├── frontend/         # React + Vite
├── docker/           # Dockerfiles, nginx.conf
├── docker-compose.yml
└── scripts/          # setup.sh, run_tests.sh
```
