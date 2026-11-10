# Changelog

## 1.3.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- MCP (Model Context Protocol) server for agent memory system
- Four memory tools: memory_read, memory_write, memory_list, memory_delete
- MCP server runs over stdio for external AI integration
- POST /api/agents/mcp/run endpoint for server info
- Backend tests for MCP server initialization and endpoint

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

### Added
- LLM chat integration for agents with provider-agnostic adapters
- POST /api/agents/{id}/chat endpoint for chat completions
- Frontend API client types and functions for chat
- Backend tests for chat endpoint (3 new tests)

### Security

Partial code published for continued development. Known issues: STATUS.md.

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [1.0.0] - 2026-10-21

### Added
- FastAPI backend with SQLite persistence
- React + TypeScript + Vite frontend
- Agent CRUD API with workspace isolation
- File read/write/list operations within agent workspaces
- OIDC/Keycloak authentication stub with demo mode
- Health and readiness endpoints
- Backend pytest tests (11 tests)
- Frontend vitest tests (5 tests)
- Dockerfiles for backend and frontend
- Docker Compose for local deployment
- Comprehensive README and documentation

### Security
- Strict agent workspace sandbox (path traversal blocked)
- Demo mode restricted to localhost only
- Production mode refuses to start with demo mode enabled
- No hardcoded secrets or credentials

### Testing
- Backend: 19 passing tests (health, agents CRUD, workspace isolation, file operations, LLM chat)
- Frontend: 5 passing tests (AgentList component)
- TypeScript typecheck and build pass

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
