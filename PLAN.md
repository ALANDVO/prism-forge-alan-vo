# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton-fastapi-react

## Roadmap

### skeleton-fastapi-react — Runnable FastAPI + React skeleton with SQLite, OIDC stub, and one end-to-end workflow

Status: done

Acceptance:
- Backend FastAPI app starts and serves /api/health
- Frontend Vite React app builds and serves
- SQLite database with agents table created on startup
- OIDC/Keycloak auth stub with demo mode
- One complete workflow: create agent -> list agents -> get agent detail
- Backend tests pass (pytest)
- Frontend typecheck and build pass
- Dockerfiles for backend and frontend

Implementation: `backend/app/main.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/core/security.py`, `backend/app/models/agent.py`, `backend/app/services/agent_service.py`, `backend/app/api/routes/health.py`, `backend/app/api/routes/agents.py`, `backend/app/llm/__init__.py`, `backend/app/llm/base.py`, `backend/app/llm/openai_compatible.py`, `backend/app/llm/anthropic.py`, `backend/app/llm/gemini.py`, `backend/app/llm/factory.py`, `frontend/src/main.tsx`, `frontend/src/App.tsx`, `frontend/src/index.css`, `frontend/src/api/client.ts`, `frontend/src/components/AgentList.tsx`, `frontend/src/components/AgentForm.tsx`, `frontend/src/components/AgentDetail.tsx`

Tests: `backend/tests/test_health.py`, `backend/tests/test_agents.py`, `backend/tests/conftest.py`, `frontend/tests/Dashboard.test.tsx`, `frontend/tests/setup.ts`

### agent-workspace-isolation — Strict agent workspace sandbox (issue #1160)

Status: done

Acceptance:
- Each agent confined to its own workspace directory
- Cross-agent file operations return permission error
- Path traversal attempts blocked

Implementation: `backend/app/services/agent_service.py`, `backend/app/api/routes/agents.py`

Tests: `backend/tests/test_agents.py::test_agent_workspace_isolation`, `backend/tests/test_agents.py::test_agent_file_operations`

### mcp-tool-exposure — MCP tool exposure for agent memory system (issue #322)

Status: planned

Acceptance:
- MCP server exposes agent memory tools
- External AI can call tools via MCP protocol
- Tools work independently of main UI

### onnxruntime-windows-compat — Defensive onnxruntime/fastembed loading for Windows compatibility (issue #2072)

Status: planned

Acceptance:
- Startup preload of optional native deps
- Graceful degradation on import failure
- Documented Windows version requirements

### postgres-pool-resilience — PostgreSQL connection pool liveness checks (issue #1172)

Status: planned

Acceptance:
- Connection pool configured with check= probe
- Explicit max_lifetime configured
- Retry logic for transient connection errors

