# ReanMore v2.1 Master Implementation Plan

> **Authoritative Specification:** [`docs/ReanMore_Architecture_v2.1.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/ReanMore_Architecture_v2.1.md)  
> **Status:** APPROVED ARCHITECTURE — READY FOR EXECUTION  
> **Target Release:** v2.1 (English-first MVP, Local Primary Model, Thin Vertical Slice)  
> **Target Hardware:** Single Workstation / Laptop (AMD Ryzen 9 / Intel Core i7, 16 GB RAM, RTX 4050 6 GB VRAM or CPU execution)

---

## 1. Executive Summary & Scope Boundary

The objective of the ReanMore v2.1 implementation is to transform the existing multi-container prototype into a **streamlined, constrained agentic Socratic tutoring system** tailored specifically for elementary students in Grades 1-6 tackling Mathematics homework.

### 1.1 The Thin Vertical Slice Scope Cut (Phase 1 MVP)

| Dimension | Legacy / Overengineered Prototype | Phase 1 MVP Scope (Thin Vertical Slice) | Status in Phase 1 MVP |
| :--- | :--- | :--- | :--- |
| **Input Modality** | Typed text + Photo OCR + Voice | **Typed math input + tap-to-build widget** | Photo OCR deferred to Phase 4 |
| **Subject Scope** | Math + Science (Bio/Chem/Phys) | **Mathematics only (Grades 1-6)** | Science RAG deferred to Phase 3 |
| **Model Runtime** | Cold-swapping primary + failover | **Single resident model (`qwen3.5:4b`) + template fallback** | Zero cloud API dependencies ($0.00/query) |
| **Visual Scaffolding** | Prototype widgets / text emojis | **Deterministic SVG `VisualSpec` (6 models)** | 100% deterministic math generation |
| **Infrastructure** | 9 distributed containers | **4 containers (Orchestrator, Postgres, Ollama, Frontend)** | Redis, MinIO, Qdrant pruned |
| **Math Engine** | Separate microservice (:9001) | **In-process SymPy CAS inside orchestrator** | Eliminates inter-service network hop |
| **Quota System** | Daily + Monthly, Redis counters | **Daily quota only (10/day) via PostgreSQL ledger** | Resets 00:00 Asia/Phnom_Penh (UTC+7) |
| **Turn Locking** | Redis distributed mutex | **Per-session `asyncio.Lock` + Postgres advisory lock** | In-process concurrency control |
| **Observability** | Fragmented logs & ad-hoc tables | **Unified `gap_events` table + weekly admin digest** | Content, Learner, and System gaps |
| **Language Target** | English + partial Khmer stubs | **100% English-first** | Khmer NLP deferred to v2.2 |

---

## 2. System Architecture Audit Matrix (Current System vs Architecture v2.1)

Audited against `ReanMore_Architecture_v2.1.md` using the `architecture-auditor` taxonomy: `MATCHES`, `PARTIAL`, `MISSING`, `CONFLICTS`, `EXTRA`.  
> **Quick Reference:** See [`docs/plans/README.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/README.md) for the developer handoff and verification guide.

### 2.1 Boundary Contracts & Endpoints (L1)

| Contract / Endpoint | Target Architecture v2.1 Spec | Current Code Implementation | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| `POST /api/query` | Socratic query turn; dual-payload (markdown + `step_widget` with `VisualSpec`); quota check | Routes to `socratic_graph`; handles session persistence; emits markdown + `step_widget` | `MATCHES` | [`endpoints.py:L234-658`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L234-L658) |
| `POST /api/step/navigate` | Step navigation (dots / buttons); free from quota deduction | Step navigation logic; free navigation intact; updates `current_step_index` | `MATCHES` | [`endpoints.py:L666-777`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L666-L777) |
| `POST /api/step/answer` | Step evaluation; validates student answer; updates attempts & hints | Validates step answer via rubric / equivalence; triggers hint or advance | `MATCHES` | [`endpoints.py:L779-863`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L779-L863) |
| `POST /api/step/validate` | Non-directional near-miss evaluation via `validate_student_answer` | Direct rubric integration; non-directional cues | `MATCHES` | [`endpoints.py:L873-903`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L873-L903) |
| `POST /api/session/sync` | Frontend state reconciliation & rehydration | Rehydrates session from database and returns current state | `MATCHES` | [`endpoints.py:L957-1033`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L957-L1033) |
| `GET /api/system-prompt` | System prompt calibration debug endpoint | Returns prompt configuration | `MATCHES` | [`endpoints.py:L1147-1160`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L1147-L1160) |
| `POST /api/translate` | Legacy translation route | Khmer-English translation hook (deferred to v2.2) | `EXTRA` | [`endpoints.py:L218-230`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py#L218-L230) |

### 2.2 Socratic State & Orchestration (L2)

| State / Node Component | Target Architecture v2.1 Spec | Current Code Implementation | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| `TutorState` Contract | Persistent TypedDict context; `step_widget`, `current_hint_tier`, `attempt_history`, RAG | Complete TypedDict defined in `state.py`; matches all required keys | `MATCHES` | [`state.py:L29-106`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/state.py#L29-L106) |
| `SocraticStep` Schema | 4-Part card schema: Mission, Clue, Helpful Example, Your Turn | Adheres strictly to 4-Part Card format; includes `visual_data` field | `MATCHES` | [`card_schema.py:L11-64`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/card_schema.py#L11-L64) |
| `Word Problem Verifier` | 7-stage parse verifier + free child confirmation prompt | Deterministic operand check, coverage check, operator sanity | `MATCHES` | [`parse_verifier.py:L1-150`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/parse_verifier.py#L1-L150) |
| `Hint Engine (3-Tier)` | Tier 1: Nudge, Tier 2: Visual, Tier 3: Parallel Worked Example | 3-tier progressive hint engine; zero answer leaks | `MATCHES` | [`hint_engine.py:L1-200`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/hint_engine.py#L1-L200) |
| `Reveal & Continue` | Exit node triggered after 3 failed attempts; reveals answer | Implemented in `reveal_and_continue.py`; clean exit logic | `MATCHES` | [`reveal_and_continue.py:L1-120`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/reveal_and_continue.py#L1-L120) |

### 2.3 Domain Engines & LLM Runtime (L3)

| Component / Subsystem | Target Architecture v2.1 Spec | Current Code Implementation | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| `Math Solver Engine` | In-process SymPy CAS + Skill Templates (`add_within_20`, etc.) | In-process CAS module inside orchestrator (`cas.py`) | `MATCHES` | [`cas.py:L1-180`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/math_engine/cas.py#L1-L180) |
| `Skill Template Library` | 6 deterministic skill templates generating steps and `VisualSpec` | 7 skills registered in `skill_registry` (`add_within_20` to `one_step_word_problem`) | `MATCHES` | [`skills/__init__.py:L1-33`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/skills/__init__.py#L1-L33) |
| `VisualSpec Generator` | Deterministic SVG JSON schema generator (6 visual models) | 6 SVG builders with answer-safe vs reveal modes | `MATCHES` | [`visual_spec.py:L1-260`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/visual_spec.py#L1-L260) |
| `Leak Guard v2` | Allowlist for given operands; 6-token disclosure window; visual check | Leak Guard v2 scans prose & visual labels; 100/100 adversarial test probes pass | `MATCHES` | [`leak_guard.py:L1-350`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/guardrails/leak_guard.py#L1-L350) |
| `Science RAG Engine` | Local FastEmbed + Qdrant embedded; 15 curriculum chapters | FastEmbed BGE ONNX + Qdrant embedded; 30/30 golden test cases pass (100%) | `MATCHES` | [`retriever.py:L1-140`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/rag/retriever.py#L1-L140) |
| `LLM Manager & Routing` | Ollama resident (`qwen3.5:4b`) primary; semaphore `INFLIGHT=1`; 6.0s timeout | Single-model retry loop + semaphore `INFLIGHT=1` + template fallback | `MATCHES` | [`manager.py:L1-120`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/llm/manager.py#L1-L120) |
| `Legacy Math Microservice` | Deprecated (replaced by in-process SymPy CAS) | Microservice directory present; not needed in 4-container stack | `CONFLICTS` | [`backend/services/math_service/`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/services/math_service/) |
| `Legacy Science Microservice`| Deprecated (replaced by in-process Science RAG) | Microservice directory present; not needed in 4-container stack | `CONFLICTS` | [`backend/services/science_service/`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/services/science_service/) |

### 2.4 Ingress, Storage & Infrastructure (L4)

| Infrastructure Area | Target Architecture v2.1 Spec | Current Code Implementation | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| `Container Topology` | 4 containers: Orchestrator, Postgres, Ollama, Frontend | 4 streamlined containers in docker-compose.yml | `MATCHES` | [`docker-compose.yml:L1-90`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/docker-compose.yml#L1-L90) |
| `Daily Quota System` | 10 problems/day; Postgres ledger; Phnom Penh reset; free hints | Implemented with Redis + in-memory fallback + Postgres ledger | `MATCHES` | [`quota_guard.py:L27-74`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/quota/quota_guard.py#L27-L74) |
| `Unified Gap Accounting` | `gap_events` table (content, learner, system) + `gap_summary` view | Unified `gap_events` table + `gap_summary` view + async dispatcher | `MATCHES` | [`database.py:L106-155`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/infrastructure/database.py#L106-L155) |
| `Admin Audit Digest` | Weekly Monday morning digest CLI script | Standalone script with priority scoring and markdown generation | `MATCHES` | [`generate_admin_digest.py:L1-200`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/scripts/generate_admin_digest.py) |
| `Frontend Visual Renderer` | Pure SVG `<VisualRenderer />` consuming backend `VisualSpec` | Pure React SVG components (6 models) dispatching via VisualWidget | `MATCHES` | `frontend/src/components/visual/` |
| `Homework OCR Ingress` | Deferred to Phase 4 (Typed math input & tap-to-build for MVP) | Standalone OCR module and endpoints in active routing | `EXTRA` | `backend/homework_ocr_vlm/` |

---

## 3. Subsystem Execution Roadmap & Dependency Graph

```text
┌────────────────────────────────────────────────────────────────────────┐
│                   PHASED EXECUTION DEPENDENCY GRAPH                     │
└────────────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 0: Benchmarks & Runtime [COMPLETED ✅]   │
          │  - LLM_MAX_INFLIGHT = 1 semaphore (Done)       │
          │  - Streaming first-token timeout (Done)         │
          │  - Workstation benchmark suite (Done)           │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 1A: Math & Skills [COMPLETED ✅]          │
          │  - In-process SymPy CAS engine (Done)           │
          │  - 6 deterministic skill templates (Done)       │
          │  - Word problem parse verification (Done)       │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 1B: VisualSpec & SVG [COMPLETED ✅]       │
          │  - Backend VisualSpec schema (6 models) (Done)  │
          │  - Answer-safe mode isolation (Done)            │
          │  - Pure React SVG <VisualRenderer /> (Done)     │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 1C: Leak Guard v2 [COMPLETED ✅]         │
          │  - Given operands allowlist (Done)              │
          │  - 6-token disclosure window check (Done)       │
          │  - VisualSpec security scanner (Done)           │
          │  - 100-case adversarial test suite (Done)       │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 1D: Unified Gap Accounting [COMPLETED ✅] │
          │  - gap_events table & gap_summary view (Done)   │
          │  - Telemetry hooks (content/learner/sys) (Done) │
          │  - Weekly Monday admin audit digest script (Done│
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 1E: Streamlined 4-Container [COMPLETED ✅]│
          │  - Clean docker-compose.yml (4 containers) (Done│
          │  - Postgres-only quota & in-memory turn locks   │
          │  - Kid-friendly math keypad / tap-to-build (Done│
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 1H & 1I: Hints & Sessions [COMPLETED ✅] │
          │  - Step-specific hints array in LLM payload (Done)│
          │  - Zero extra LLM calls / 0ms hint latency (Done)│
          │  - Navigation hint sync & ReanMore prompt intact│
          │  - Ephemeral session creation on new chat/HW    │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 2: Golden Verification & Pilot [DONE ✅] │
          │  - 50 Math golden worksheets evaluation (Done)  │
          │  - 100 Adversarial leak probes (Done)           │
          │  - Real-kid pilot protocol & handbook (Done)    │
          └────────────────────────┬────────────────────────┘
                                   │
                                   ▼
          ┌─────────────────────────────────────────────────┐
          │  Phase 3: Curriculum Science RAG [COMPLETED ✅] │
          │  - FastEmbed ONNX 384-dim offline embeddings    │
          │  - Qdrant collection (15 science chapters)      │
          │  - Socratic context grounding & citation links  │
          │  - SCIENCE_OUT_OF_CURRICULUM gap logging        │
          │  - 30-case golden benchmark (100% retrieval)    │
          └─────────────────────────────────────────────────┘
```

---

## 4. Subsystem Execution Plans (Document Breakdown)

The detailed engineering plans are divided into modular, actionable documents in [`docs/plans/`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/):

1. [`phase0_benchmarks_and_runtime.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase0_benchmarks_and_runtime.md) — **COMPLETED & VERIFIED ✅**  
   *Hardware benchmarking, resident Ollama configuration, `LLM_MAX_INFLIGHT=1` semaphore, 6.0s streaming timeout, and concurrency stress testing.*

2. [`phase1_math_skill_templates.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase1_math_skill_templates.md) — **COMPLETED & VERIFIED ✅**  
   *In-process SymPy CAS migration, 6 core elementary math skill templates (`add_within_20` to `one_step_word_problem`), and the 7-stage word problem parse verifier with child confirmation.*

3. [`phase1_visual_spec_engine.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase1_visual_spec_engine.md) — **COMPLETED & VERIFIED ✅**  
   *Deterministic `VisualSpec` schema, 6 SVG builders (`ten_frame`, `number_line`, `base_ten_blocks`, `array_grid`, `fraction_bar`, `bar_model`), and frontend `<VisualRenderer />` implementation.*

4. [`phase1_leak_guard_v2.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase1_leak_guard_v2.md) — **COMPLETED & VERIFIED ✅**  
   *Leak Guard v2 upgrade: given operand allowlist, scoped target verification, structural example check, 6-token disclosure window, and visual spec security scanning.*

5. [`phase1_unified_gap_report_and_db.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase1_unified_gap_report_and_db.md) — **COMPLETED & VERIFIED ✅**  
   *PostgreSQL migration for `gap_events` and `gap_summary`, multi-tier telemetry logging, priority ranking formula, and the weekly Monday admin digest script.*

6. [`phase1_streamlined_infra_and_frontend.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase1_streamlined_infra_and_frontend.md) — **COMPLETED & VERIFIED ✅**  
   *Streamlining from 9 containers to 4, Postgres-only quota guard (10/day), in-memory turn locks, and kid-friendly UI enhancements.*

7. [`phase2_golden_eval_and_pilot.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase2_golden_eval_and_pilot.md) — **COMPLETED & VERIFIED ✅**  
   *50 golden math worksheets evaluation (100% pass, 0 leaks), 100 adversarial leak probes (100% quarantined), and 8-student real-kid classroom pilot protocol with teacher observation handbook.*

8. [`phase3_curriculum_science_rag.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/plans/phase3_curriculum_science_rag.md) — **COMPLETED & VERIFIED ✅**  
   *Local Qdrant vector store, offline dense embeddings (FastEmbed bge-small-en-v1.5), 15 elementary science curriculum units (Life, Physical, Earth & Space), Socratic context grounding, content gap logging, 30-case golden science benchmark suite (100% retrieval success), and 5/5 Pytest unit tests.*

---

## 5. Change Control Invariants & Sacred Contracts

In accordance with the `change-control` and `no-mock-guardian` engineering guidelines:

1. **Sacred File Inviolability:**
   - [`endpoints.py`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/api/endpoints.py): Route signatures (`/api/query`, `/api/step/navigate`, `/api/step/answer`, `/api/step/validate`) must not alter public signatures or HTTP methods.
   - [`state.py`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/socratic/state.py): `TutorState` dictionary keys must not be renamed or deleted without prior audit approval.
   - Dual-payload response contract (`markdown` + `step_widget`) must remain backwards-compatible for the frontend.
2. **Subsystem-by-Subsystem Isolation:**
   - Never refactor multiple subsystems in a single step. Complete tests and verify 100% green before proceeding to the next subsystem.
3. **Continuous Test Verification:**
   - Run `& ..\.venv\Scripts\python.exe -m pytest testing/unit/ -v` from `backend/` after every subsystem step.
4. **No-Mock Rule:**
   - Zero canned answers or fake solutions in production services. If Ollama or the local CAS is down or overloaded, return structured honest degradation (`success=False, error=...`).
5. **Git Archive Protocol:**
   - Before pruning legacy components (`backend/services/science_service/`, `backend/homework_ocr_vlm/`), create dedicated git archive branches/tags (`archive/science-service`, `archive/homework-ocr-vlm`).
