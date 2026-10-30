# Legacy Archive

This directory holds code that is no longer part of the v2.1 MVP (4-container
topology: Orchestrator, PostgreSQL, Ollama, Frontend). Nothing here is imported
by the production tree, the CI suite, or `backend/testing/`.

## `microservices/`

| Path | Reason archived |
| :--- | :--- |
| `services/math_service/` | Replaced by the in-process SymPy CAS in `backend/orchestrator/app/services/socratic/math_engine/`. |
| `services/science_service/` | Replaced by in-process Science RAG; not part of the 4-container MVP. |
| `tests/test_solvers.py` | Unit tests for the archived microservices only. |
| `tests/test_math_solver.py` | Tests for the archived math microservice (`app.solvers.algebra`). |

## `stray-root/`

Stale copies of `orchestrator/`, `testing/`, `services/`, and `ingestion/` that
duplicated `backend/` at the repository root, plus the old 7-service root
`docker-compose.legacy.yml`. They were untracked and could shadow real packages
via `pythonpath = orchestrator . ..`; they are preserved here for reference.

## Restoring

Restore by moving a directory back into the tree and re-adding its tests to the
pytest paths. The archived microservices use the deprecated bare `app.*` import
fallback, so they must be run with their own service directory on `sys.path`.
