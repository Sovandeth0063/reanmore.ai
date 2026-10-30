# Phase 1E Implementation Plan: Streamlined 4-Container Topology & Frontend Integration

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](../../docs/ReanMore_Architecture_v2.1.md) (Sections 2, 5.4, 5.5, 9, 12.1, 12.2)  
> **Status:** COMPLETED & VERIFIED ✅  
> **Prerequisites:** Phases 1A through 1D complete.

---

## 1. Objectives & Scope

Phase 1E consolidates the system infrastructure from a brittle 9-container prototype into a robust **4-container deployment** capable of running offline on a single 16 GB RAM / 6 GB VRAM workstation, while finishing the kid-friendly frontend web experience:
1. **Streamline Docker Compose:** 4 containers only (`orchestrator`, `postgres`, `ollama`, `frontend`).
2. **Postgres-Only Quota & State:** Replace Redis session cache with PostgreSQL ledger and in-memory `asyncio.Lock` turn guards.
3. **Daily Quota Enforcement:** Strict 10 problems/day per student in `Asia/Phnom_Penh` (UTC+7); hints, steps, and answer checks remain 100% free.
4. **Kid-Friendly Frontend Interface:** Math input bar, tap-to-build problem builder, and queue notification banner ("You're next! 🌟").

---

## 2. Current State vs Target Architecture

| Component | Current Implementation | Target Specification | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| **Container Count** | 9 distributed containers (Redis, Qdrant, MinIO, Math, Science, etc.) | 4 containers (Orchestrator, Postgres, Ollama, Frontend) | `CONFLICTS` | [`docker-compose.yml:L1-136`](../../backend/docker-compose.yml#L1-L136) |
| **Turn Locking** | Redis distributed mutex | Per-session in-memory `asyncio.Lock` + Postgres advisory lock | `PARTIAL` | [`session.py:L1-80`](../../backend/orchestrator/app/services/session.py#L1-L80) |
| **Quota Cache** | Redis fast-path counters + Postgres fallback | PostgreSQL ledger as single source of truth | `PARTIAL` | [`quota_guard.py:L18-24`](../../backend/orchestrator/app/services/quota/quota_guard.py#L18-L24) |
| **Frontend Stepper** | Ad-hoc widget mounting | Unified stepper integrating `<VisualRenderer />` | `PARTIAL` | [`App.tsx:L1-200`](../../frontend/src/App.tsx#L1-L200) |

---

## 3. Step-by-Step Implementation Steps

### Step 1E.1: Streamlined `docker-compose.yml`

Refactor `backend/docker-compose.yml` to define strictly 4 containers:

```yaml
version: '3.8'

services:
  # 1. System of Record: PostgreSQL 16 Alpine
  db:
    image: postgres:16-alpine
    container_name: reanmore-postgres
    restart: always
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-postgres}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-postgres}
      POSTGRES_DB: ${POSTGRES_DB:-science_chatbot}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - reanmore-network
    deploy:
      resources:
        limits:
          memory: 2048M

  # 2. Local Resident Model: Ollama Server
  ollama:
    image: ollama/ollama:latest
    container_name: reanmore-ollama
    restart: always
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - reanmore-network
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: all
              capabilities: [gpu]

  # 3. Core Socratic Orchestrator Gateway (FastAPI with in-process SymPy CAS)
  orchestrator:
    build:
      context: ./orchestrator
      dockerfile: Dockerfile
    container_name: reanmore-orchestrator
    restart: always
    ports:
      - "9000:9000"
    env_file:
      - .env
    environment:
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/science_chatbot
      - OLLAMA_BASE_URL=http://ollama:11434
      - LLM_PRIMARY_PROVIDER=ollama
      - OLLAMA_MODEL=qwen3.5:4b
    depends_on:
      - db
      - ollama
    networks:
      - reanmore-network
    deploy:
      resources:
        limits:
          memory: 1536M

  # 4. Frontend Web App (Nginx serving React Vite build)
  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: reanmore-frontend
    restart: always
    ports:
      - "80:80"
      - "3000:80"
    depends_on:
      - orchestrator
    networks:
      - reanmore-network
    deploy:
      resources:
        limits:
          memory: 256M

volumes:
  postgres_data:
  ollama_data:

networks:
  reanmore-network:
    driver: bridge
```

### Step 1E.2: Postgres-Only Quota Guard

In `backend/orchestrator/app/services/quota/quota_guard.py`:
- Make Redis an optional optimization; default to querying the `usage_ledger` PostgreSQL table directly:
  ```python
  # Count problems solved today in Asia/Phnom_Penh (UTC+7)
  async def get_daily_usage(user_id: str, date_str: str) -> int:
      # Direct SQL count on usage_ledger where created_at >= midnight_phnom_penh
  ```
- Guarantee that:
  - Hints, step navigations, and answer checks execute without checking or deducting problem quota.
  - Quota deduction occurs only upon successful milestone decomposition of a new problem.

### Step 1E.3: In-Memory Turn Locking

In `backend/orchestrator/app/services/session.py`:
- Maintain an in-memory dictionary of session locks:
  ```python
  class SessionTurnLockManager:
      def __init__(self):
          self._locks: Dict[str, asyncio.Lock] = {}

      def get_lock(self, session_id: str) -> asyncio.Lock:
          if session_id not in self._locks:
              self._locks[session_id] = asyncio.Lock()
          return self._locks[session_id]
  ```
- Protect `/api/query` and `/api/step/answer` turns with `async with lock_manager.get_lock(session_id):` to prevent interleaved race conditions.

### Step 1E.4: Frontend Kid-Friendly UI Enhancements

In `frontend/src/`:
1. **Math Keyboard & Tap-to-Build Widget:**
   - Visual keypad with large buttons: digits `0-9`, operators `+`, `-`, `×`, `÷`, fractions `½`, `¼`, and symbols `=`.
   - Tap-to-build prompt chips: *"I want to add..."*, *"Help me with fractions..."*.
2. **Mount `<VisualRenderer spec={step.visual_data} />`:**
   - Display the visual model directly under the "Helpful Picture / Example" card section.
3. **Queue Notification Toast / Banner:**
   - Listen for `queue_status` events: display cheerful toast: *"You're next in line! 🌟"* with animated progress dots.
4. **Honest Resting State:**
   - If local model is unreachable or timed out, display friendly resting message: *"My thinking engine is taking a quick rest! Let's try once more in a moment. 🌟"*.

---

## 4. Verification & Testing Protocol

Execute end-to-end stack verification:

```powershell
# 1. Start streamlined 4-container stack
cd backend
docker-compose up -d --build

# 2. Verify all 4 containers healthy
docker-compose ps

# 3. Execute full backend unit & integration tests against local environment
& ..\.venv\Scripts\python.exe -m pytest testing/unit/ -v
```

### Exit Criteria
- [x] 4 containers start cleanly and consume $< 4.5$ GB host RAM combined.
- [x] Redis, MinIO, and Qdrant containers are fully deactivated for Phase 1 MVP.
- [x] Quota ledger operates purely in PostgreSQL and resets at midnight Phnom Penh time.
- [x] Frontend renders 4-part cards and deterministic SVG visual models smoothly.
