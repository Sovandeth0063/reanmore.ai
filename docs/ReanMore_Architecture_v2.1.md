# Agentic AI Architecture Specification: ReanMore

Socratic STEM Homework Tutor for Grades 1-6 · v2.1 (English-first MVP, Local Primary Model, Thin Vertical Slice)

## TL;DR

**ReanMore** v2.1 refactors a multi-container prototype into a **streamlined, constrained agentic Socratic tutoring system** engineered specifically for elementary students in Grades 1-6 tackling Mathematics homework. Students type questions or use a kid-friendly tap-to-build problem interface. ReanMore decomposes problems into 2-4 bite-sized pedagogical milestones, enforces 3-tier progressive hints paired with **deterministic SVG visual models** (e.g., ten-frames, base-ten blocks, number lines), and strictly prevents direct answer disclosure. 

The Phase 1 MVP operates **100% offline** on a single developer workstation or classroom PC using **Ollama** (`qwen3.5:4b`) as the primary resident model with zero cloud API costs. Model failover follows a single-model retry and deterministic **Skill Template** ladder (no memory-busting cold swaps). Mathematical equivalence is computed deterministically via an in-process SymPy CAS engine; word problems pass strict parse verification with child confirmation; and **Leak Guard v2** prevents premature answer leaks across text and visual payloads. All system anomalies, learner misconceptions, and missing curriculum skills feed into a **Unified Gap Report** (`gap_events`) delivering a weekly actionable digest to teachers and engineers.

| Key Metric | Value |
| :--- | :--- |
| **Target Hardware** | Single Workstation / Laptop (AMD Ryzen 9 / Intel Core i7, 16 GB RAM, RTX 4050 6 GB VRAM or CPU execution) |
| **Primary Model** | `qwen3.5:4b` via Ollama — 3.4 GB resident in memory (pinned by digest; fast local token generation) |
| **Failover Ladder** | Single model retry -> Skill Template hint fallback -> Honest resting notice (fits within 6 GB VRAM) |
| **Active Language** | **100% English (v2.1 MVP)**; unspaced Khmer script segmentation, tokenization, & curricula deferred to v2.2 |
| **MVP Input Mode** | **Typed math input & tap-to-build widget**; worksheet photo OCR deferred to Phase 4 |
| **MVP Subject Scope** | **Mathematics only (Grades 1-6)**; curriculum Science RAG deferred to Phase 3 |
| **Deployment Cost** | **$0.00 per query** (100% offline, private, open-source stack; zero cloud API dependencies) |
| **Visual Scaffolding** | Deterministic SVG specs (`ten_frame`, `number_line`, `base_ten_blocks`, `array_grid`, `fraction_bar`, `bar_model`) |
| **Pedagogical Invariant** | 0 leaks on release suite (statistical target; monitored via `leak_guard_interceptions_total` & audits) |
| **Math Parity** | 100% symbolic & arithmetic accuracy via SymPy CAS; LLM never performs raw arithmetic |
| **Parse Verification** | Operand presence, number coverage, and operator sanity checks + free child confirmation prompt |
| **Daily Problem Quota** | 10 new problems/day per student (PostgreSQL ledger; resets at 00:00 Asia/Phnom_Penh, UTC+7) |
| **Free Interactivity** | Hints, step navigation, "explain more", answer checks, and parse clarifications are 100% free |
| **Latency Targets** | Normal path P50: 2.5 s - 4.5 s; first-token timeout: 6.0 s; max output tokens: 220 (`num_predict`) |
| **Hard Turn Deadline** | 15.0 s strict total timeout per turn |
| **Concurrency Control** | Bounded semaphore (`LLM_MAX_INFLIGHT = 1`) with friendly queue state ("You're next! 🌟") |
| **MVP Infrastructure** | **4 containers:** Orchestrator (in-process math) + PostgreSQL + Ollama + Frontend (Nginx/Vite) |
| **Evaluation Suite** | 50 Math golden worksheets | 100 Adversarial leak cases | 6-10 student real-kid pilot protocol |

## How to read this document

The numbered sections (1-14) define the architectural decisions, operational contracts, state machines, and request flows (approximately 25 minutes to read). Section 15 outlines the strict phased implementation roadmap (Phases 0 through 5). The [appendices](#appendices) hold technical deep dives, database models, repository implementations, configuration manifests, prompt specifications, and the exhaustive repository layout.

<a id="contents"></a>
**Contents**

1. [Overview](#1-overview)
2. [Scope cut: thin vertical slice](#2-scope-cut-thin-vertical-slice)
3. [Architecture at a glance](#3-architecture-at-a-glance)
4. [Components](#4-components)
5. [Request flow](#5-request-flow) (incl. [5.2 Word problem parse verification](#52-word-problem-parse-verification-pipeline), [5.3 Runtime failover ladder](#53-runtime-failover-ladder-and-concurrency-control), [5.4 Resumable streaming & quota](#54-resumable-streaming-and-usage-limits), [5.5 In-memory queue](#55-student-message-queue-while-answering))
6. [Tech stack](#6-tech-stack)
7. [Math engine & Skill template library](#7-math-engine--skill-template-library) (incl. [7.1 Skill template contract](#71-skill-template-contract), [7.2 6 MVP math skills](#72-the-6-mvp-math-skills))
8. [Visual explanation generator spec](#8-visual-explanation-generator-spec) (incl. [8.1 VisualSpec schema](#81-visualspec-schema), [8.2 Deterministic visual leak check](#82-deterministic-visual-leak-check))
9. [Data, memory, and storage](#9-data-memory-and-storage) (incl. [9.1 TutorState lifecycle](#91-socratic-tutorstate-lifecycle-and-student-session-state))
10. [Security and guardrails](#10-security-and-guardrails) (incl. [10.1 Leak Guard v2](#101-leak-guard-v2-specification), [10.2 Roster-based PII scrubbing](#102-roster-based-pii-scrubbing-and-privacy), [10.3 PIN authentication](#103-pin-authentication-hardening))
11. [Observability and Unified Gap Report](#11-observability-and-unified-gap-report) (incl. [11.1 Gap taxonomy](#111-unified-gap-taxonomy-content-learner-system), [11.2 PostgreSQL schema](#112-postgresql-gap_events-schema), [11.3 Weekly admin audit digest](#113-weekly-admin-audit-digest))
12. [Deployment and CI/CD](#12-deployment-and-cicd) (incl. [12.1 Streamlined 4-container topology](#121-streamlined-4-container-topology), [12.2 Container resource limits](#122-container-resource-limits))
13. [Repository layout](#13-repository-layout)
14. [Risks, open questions & decision log](#14-risks-open-questions--decision-log)
15. [Phased roadmap & evaluation with real kids](#15-phased-roadmap--evaluation-with-real-kids)
16. [Appendices](#appendices)

[**Appendices:**](#appendices) [A. Detailed protocol diagram](#appendix-a-detailed-protocol-diagram) | [B. Storage tiers & Repository interfaces](#appendix-b-storage-tiers--repository-interfaces) | [C. Skill templates & parse verification code](#appendix-c-skill-templates--parse-verification-code) | [D. Dynamic prompt engine & Socratic card templates](#appendix-d-dynamic-prompt-engine--socratic-card-templates) | [E. Local runtime implementation and concurrency control](#appendix-e-local-runtime-implementation-and-concurrency-control) | [F. Model router configuration](#appendix-f-model-router-configuration) | [G. Cost and hardware budget breakdown](#appendix-g-cost-and-hardware-budget-breakdown) | [H. Leak Guard v2 engine & test harness](#appendix-h-leak-guard-v2-engine--test-harness) | [I. Full repository tree](#appendix-i-full-repository-tree)

---

## 1. Overview

| Attribute | Specification |
| :--- | :--- |
| **Product Name** | **ReanMore** ("Learn More" / រៀនបន្ថែម) |
| **Authority / Sponsor** | Khmer Enterprise (KE) & Ministry of Education, Youth and Sport (MoEYS) STEM Initiative |
| **Target Audience** | Primary: Grades 1-3 (Early Childhood / Basic Arithmetic & Addition/Subtraction); Secondary: Grades 4-6 (Multiplication, Fractions, Word Problems) |
| **Pedagogical Model** | Strict Socratic Scaffolding: 4-part step cards (Mission, Clue, Helpful Example, Your Turn), 3-tier progressive hints, deterministic SVG visual models, Reveal & Continue fallback |
| **Language Strategy** | **100% English-first in v2.1 MVP.** All Socratic cards, hints, questions, and templates are formulated strictly in English. Khmer script segmentation, unspaced tokenization, and bilingual UI hooks are architected and deferred to v2.2. |
| **Hosting & Execution** | **100% Local Offline Workstation.** Sized specifically for developer workstations or school lab servers (AMD Ryzen / Intel Core, 16 GB RAM, RTX 4050 6 GB VRAM or CPU execution) with zero external cloud API dependencies. |
| **Integrity Rule** | **Never Fakes It:** No mocks, no stubs, no fake solvers in production. Dependencies degrade gracefully with structured, honest status notices. Failed turns never charge student quota. |
| **Version** | v2.1 (Socratic Agentic Architecture, Thin Vertical Slice, Local Ollama Primary, Leak Guard v2) |

---

## 2. Scope cut: thin vertical slice

**Goal of MVP:** Prove that an elementary student can type a math problem, get step-by-step Socratic guidance paired with an interactive visual model, never receive the final answer prematurely, and produce rich, actionable gap data for teachers and engineers. Nothing else.

| Architectural Area | v2.1 Draft (Overengineered) | Phase 1 MVP (Thin Vertical Slice) | Later Phase Expansion |
| :--- | :--- | :--- | :--- |
| **Input Mode** | Typed + photo OCR ingress | **Typed math input + tap-to-build widget** | Photo OCR upload (Phase 4) |
| **Subject Scope** | Math + Science RAG | **Mathematics only (Grades 1-6)** | Science curriculum RAG (Phase 3) |
| **Model Runtime** | Cold-swapping primary + failover | **Single resident model (`qwen3.5:4b`) + template fallback** | Dual-model if measured to fit VRAM |
| **Visual Scaffolding**| Plain text emoji analogies | **Deterministic SVG VisualSpec (6 core types)** | Advanced animated visuals |
| **Infrastructure** | 9 distributed containers | **4 containers (Orchestrator, Postgres, Ollama, Frontend)** | Redis, Qdrant, MinIO when needed |
| **Math Engine** | Separate microservice (:9001) | **In-process Python module inside orchestrator** | Microservice if distributed scaling needed |
| **Stream Resilience** | Redis Streams buffer | **Plain SSE; client refetches state from PostgreSQL on reconnect**| Redis Streams in Phase 5 |
| **Turn Locking** | Redis distributed mutex | **Per-session `asyncio.Lock` (in-memory) / Postgres advisory lock**| Redis mutex if multi-node |
| **Quota Enforcement**| Daily + monthly, Redis counters | **Daily quota only (10 problems/day) via PostgreSQL ledger** | Monthly cap if classroom data warrants |
| **Languages** | English + partial Khmer stubs | **100% English focus** | Khmer script normalizer (v2.2) |

**Rationale:** Redis, Qdrant, and MinIO each solve distributed multi-node scaling, document vector retrieval, and binary image storage. In the Phase 1 Math MVP, none of those problems exist yet. Pruning them eliminates operational failure points and ensures rock-solid classroom demos.

---

## 3. Architecture at a glance

```text
              Grades 1-6 Students | Classroom Teachers | Parents | Admins
                                         |
                        React 18 Stepper UI / Mobile Web PWA
                                         | (HTTPS / SSE Streaming)
                                         v
+===================================================================================+
| API Gateway & Socratic Orchestrator (FastAPI :9000)                                |
| - Class Code + 4-digit PIN Authentication (argon2id, lockout after 5 fails)       |
| - In-Memory Session Turn Lock (`asyncio.Lock`) & Bounded Semaphore (`INFLIGHT=1`) |
| - Two-Phase Quota Guard: Check / Commit (10 problems/day in Asia/Phnom_Penh)      |
| - Server-Sent Events (SSE) Stream Dispatcher with Client Reconnect Rehydration     |
+----------------------------------------+------------------------------------------+
                                         |
                                         v
+===================================================================================+
| Deterministic Ingress Pre-Filter (< 10 ms, zero LLM calls)                        |
| - Roster-Based & Regex PII Scrubber (Masks Student Names, Phones, Locations)      |
| - Math Notation Sanitizer (Preserves +, -, *, /, ^, =)                            |
| - Intent & Scope Gate: Deflects off-topic chats; smalltalk instant short-circuit   |
+----------------------------------------+------------------------------------------+
                                         |
                                         v (Rehydrate TutorState from PostgreSQL)
+===================================================================================+
| Socratic LangGraph StateGraph (`orchestrator/app/services/socratic/`)             |
| - State Machine: `TutorState` TypedDict context persisted per turn                |
| - Word Problem Parse Verifier: Operand check, coverage, & child confirmation      |
| - Math Skill Registry: 6 deterministic skill templates generating steps & visuals |
| - Hint Engine: 3-tier progressive hints (Nudge -> VisualSpec -> Worked Example)   |
| - Reveal & Continue: Deterministic exit node after 3 failed attempts              |
+-------------------+-------------------------------------------+-------------------+
                    |                                           |
                    v                                           v
+---------------------------------------+   +---------------------------------------+
| In-Process Math Engine (SymPy CAS)    |   | Visual Explanation Spec Generator    |
| - Exact Symbolic Arithmetic Check     |   | - Pure Deterministic VisualSpec JSON  |
| - Algebraic AST Equivalence Validator |   | - 6 SVG Models (Ten-Frame, Bar, etc.) |
| - Target Values Isolated in Memory    |   | - Answer-Safe Mode Isolation          |
+-------------------+-------------------+   +-------------------+-------------------+
                    |                                           |
                    +---------------------+---------------------+
                                          |
                                          v
+===================================================================================+
| Single-Model LLM Runtime (Ollama Server :11434, `qwen3.5:4b` Resident)            |
| - Rephrases pedagogical card templates into encouraging, age-appropriate prose    |
| - First-Token Timeout: 6.0 s | Max Output Tokens: 220 (`num_predict`)             |
| - Single-Model Retry on Failure -> Deterministic Skill Template Fallback          |
| - $0.00 Marginal Inference Cost; 100% Workstation Local & Private                 |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+===================================================================================+
| Leak Guard v2 (`leak_guard.py`)                                                   |
| - Scans outgoing prose AND VisualSpec labels for target values & roundabout leaks |
| - Operand Allowlist: Student problem's given numbers are exempt from blocking     |
| - Structural Example Check: Verifies worked examples use distinct numbers         |
| - Word-to-Number Mapping: English words (`twelve` -> 12, `half` -> 1/2)           |
| - Narrowed 6-Token Window Disclosure Phrase Detection                             |
+-----------------------------------------+-----------------------------------------+
                                          |
                                          v
+===================================================================================+
| Dual-Payload Serializer & Storage Persistence                                    |
| - Emits `StepWidgetPayload` JSON (interactive UI stepper + SVG visual) + Markdown |
| - Commits Quota Deduction & Turn Record to PostgreSQL 16 Alpine                   |
| - Emits System, Learner, or Content Gap Events to `gap_events`                    |
| - Streams Verified Output over SSE to React Stepper UI                            |
+===================================================================================+
```

### Core Design Invariants

1. **Local Single-Model Ladder:** All natural language phrasing is handled by a single resident model (`qwen3.5:4b`) with one retry, backing up to deterministic **Skill Templates**. Zero memory-busting cold model swaps on 6 GB VRAM GPUs.
2. **Deterministic Visual Generation:** Visual models are synthesized by deterministic Python math builders, **never by the LLM**. This guarantees mathematical correctness, instantaneous rendering, and answer safety.
3. **The Socratic Invariant (Leak Guard v2):** Ground-truth answers live in isolated solver memory. Prompts on Tiers 1-3 never receive the final answer. An allowlist-aware, AST-checking Leak Guard inspects all outgoing text and visual specs.
4. **Governed Concurrency Admission:** In-memory semaphore (`LLM_MAX_INFLIGHT = 1`) queues simultaneous student turns, preventing local GPU thrashing and memory exhaustion.
5. **Word Problem Parse Verification:** LLM parse outputs undergo deterministic operand, coverage, and keyword verification. Ambiguous parses trigger a free confirmation prompt with the child.
6. **No-Mock Rule & Honest Degradation:** If an internal component or model fails, the system returns a structured degraded notice (`success=false`). Requests failing due to system issues never deduct student problem quotas.
7. **Unified Triaged Gap Accounting:** Every unhandled topic, student misconception, and system anomaly is recorded in PostgreSQL `gap_events` to drive weekly teacher digests and sprint priorities.

---

## 4. Components

| Component | Technology | Port / Location | Purpose / Responsibility | State / Persistence |
| :--- | :--- | :---: | :--- | :--- |
| **API Gateway & Orchestrator**| FastAPI / Python 3.11+ | `:9000` | Ingress routing, PIN auth, session locks, admission semaphore, dual-payload serialization, SSE streaming. | Stateless; coordinates with PostgreSQL |
| **Tier 1A Pre-Filter** | Python (deterministic) | Embedded in Gateway | Ingress sanitization, roster-based + regex PII redaction, prompt injection defense, greeting short-circuit. | Stateless |
| **System 2 Orchestrator**| LangGraph StateGraph | Embedded in Gateway | Socratic state machine, problem decomposition, step navigation, 3-tier hints, Reveal & Continue. | Checkpoints `TutorState` to PostgreSQL |
| **Math Engine** | Python / SymPy CAS | Embedded in Gateway | In-process exact symbolic arithmetic, AST equivalence checking, skill step formulation. | Stateless |
| **Skill Template Library**| Python Typed Dicts | Embedded in Gateway | 6 core elementary math skills generating deterministic steps, hints, and visual parameters. | In-memory code library |
| **VisualSpec Builder** | Python (deterministic) | Embedded in Gateway | Builds answer-safe JSON specs for ten-frames, number lines, base-ten blocks, array grids, and fraction bars. | Stateless |
| **LLM Inference Server** | Ollama (Host Workstation) | `:11434` | Hosts primary `qwen3.5:4b` resident in memory (3.4 GB VRAM); streams prose generation. | Stateless model execution |
| **Leak Guard v2** | Python (deterministic) | Embedded in Gateway | Multi-rule output barrier scanning prose and visual labels; allowlists problem operands. | Stateless |
| **Quota Guard** | Python / SQLAlchemy | Embedded in Gateway | Enforces 10 problems/day per student; two-phase check/commit; midnight Phnom Penh reset. | PostgreSQL `usage_ledger` |
| **Relational Database** | PostgreSQL 16 Alpine | `:5432` | System of record: student profiles, session logs, turn telemetry, usage ledger, unified `gap_events`. | Durable disk storage (`postgres_data/`) |
| **Frontend Web App** | React 18, Vite, TS | `:3000` | Interactive stepper widget, pure SVG `<VisualRenderer />`, kid-friendly math keyboard / tap-to-build. | Client browser state |

---

## 5. Request flow

### 5.1 Client plane: answering a student turn

Every incoming student query follows a strictly governed 10-stage execution pipeline:

| # | Stage | Component | Det? | Latency Budget | Operational Description |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **1** | **Ingress & Lock** | Gateway | Yes | < 10 ms | Validates JWT token, acquires per-session `asyncio.Lock`, acquires admission semaphore (`INFLIGHT=1`), checks 15.0 s deadline. |
| **2** | **Sanitize & PII Scrub** | Pre-Filter | Yes | < 10 ms | Roster-based exact match + regex masks names, phones, and locations; preserves math notation (`+`, `-`, `*`, `/`, `^`, `=`). |
| **3** | **Intent & Scope Gate** | System 1 | Yes | < 50 ms | Classifies intent (new problem, step attempt, hint request, navigation, greeting). Greetings/smalltalk short-circuit instantly (< 50 ms). |
| **4** | **Quota Pre-Check** | Quota Guard | Yes | < 10 ms | If `NEW_PROBLEM`: queries PostgreSQL `usage_ledger` for today's count (Asia/Phnom_Penh). If >= 10, raises HTTP 429 with encouraging reset timer. |
| **5** | **Parse & Verification** | Math Parser | Mixed | < 1.5 s | Parses word problem into structured operands and operations; validates coverage and consistency. If confidence < 0.75, asks child to confirm. |
| **6** | **Skill Dispatch** | Skill Library | Yes | < 20 ms | Matches problem to active `Skill` (e.g. `add_2digit_regroup`); builds 2-4 verified steps and generates companion `VisualSpec`. |
| **7** | **Socratic Synthesis** | LangGraph / Ollama | No | 2.0 s - 4.5 s | `qwen3.5:4b` rephrases the skill step card into kid-friendly prose (max 220 tokens). If LLM times out (> 6 s first token), retries once, then serves template text. |
| **8** | **Leak Guard v2** | Leak Guard | Yes | < 15 ms | Scans synthesized prose AND visual labels against target values, arithmetic expressions, and disclosure phrases. Blocked leaks trigger template fallback. |
| **9** | **Quota Commit & Dual Format**| Gateway / Serializer | Yes | < 15 ms | If new problem plan succeeded, commits transaction to PostgreSQL `usage_ledger`. Serializes `StepWidgetPayload` (with `VisualSpec`) + Markdown. |
| **10**| **Persist & Stream** | Gateway / Postgres | Yes | < 30 ms | Checkpoints `TutorState` to PostgreSQL; logs turn to `telemetry_logs`; releases turn lock & semaphore; streams verified tokens over SSE. |

### 5.2 Word problem parse verification pipeline

To prevent the LLM from confidently solving the wrong math expression, word problems pass through a 7-stage deterministic verification pipeline:

```text
Student Input: "Sam has 15 apples and buys 27 more apples. How many apples does Sam have?"
                                      |
                                      v
1. Structured Extraction: LLM emits JSON only:
   {"operation": "add", "operands": [15, 27], "unit": "apples", "question": "total"}
                                      |
                                      v
2. Operand Existence Check: 15 and 27 must appear verbatim or as number-words in raw input. (PASSED)
                                      |
                                      v
3. Number Coverage Check: Every number in the input must be accounted for (no unexplained numbers). (PASSED)
                                      |
                                      v
4. Keyword / Operator Sanity: Cue word "more" matches addition operation. (PASSED)
                                      |
                                      v
5. Grade Result Sanity: 15 + 27 produces positive integer 42; unit "apples" matches. (PASSED)
                                      |
          +---------------------------+---------------------------+
          | (High Confidence >= 0.75)                             | (Low Confidence < 0.75)
          v                                                       v
Immediate Skill Step Formulation               Free Child Confirmation Prompt:
                                                "Are we solving: 🍎 15 + 27 apples? [Yes] [No]"
                                                (No quota charged until child taps [Yes])
```

### 5.3 Runtime failover ladder and concurrency control

To prevent out-of-memory crashes on 6 GB GPUs, ReanMore replaces multi-model swapping with a deterministic 4-rung reliability ladder:

```text
Rung 1: Call resident `qwen3.5:4b` (streaming, first-token timeout 6.0 s, total 15.0 s)
           |
     (On Failure)
           v
Rung 2: Retry resident `qwen3.5:4b` ONCE (resident in VRAM, zero reload cost)
           |
     (On Failure)
           v
Rung 3: Serve deterministic TEMPLATE HINT from Skill Library (real pedagogical content; zero mock)
           |
     (On Failure)
           v
Rung 4: Honest degraded notice: "ReanMore is resting. Let's try again in a moment! 🌟" (Zero quota deduction)
```

**Concurrency Control (`LLM_MAX_INFLIGHT = 1`):**
Local GPUs cannot parallelize large batches without inflating KV cache memory. ReanMore enforces an in-memory `asyncio.Semaphore(1)`. If Student B sends a turn while Student A's generation is active, Student B immediately receives an in-memory queued status: *"You're next in line! 🌟 Preparing your hint..."*.

### 5.4 Resumable streaming and usage limits

- **SSE Streaming Reconnect:** The client connects to `POST /api/query` via Server-Sent Events. If the network drops, the frontend reconnects by calling `GET /api/session/{session_id}/state`. The Gateway rehydrates the latest completed step card and `TutorState` from PostgreSQL, allowing the student to resume without re-running inference.
- **Daily Quota Enforcement:** Strict limit of **10 new problems per day** per student. A problem is counted only when a new milestone plan is successfully committed to PostgreSQL `usage_ledger`. Hints, step navigations, and answer attempts are completely free. Quotas reset at 00:00 Asia/Phnom_Penh (UTC+7).

### 5.5 Student message queue while answering

If a child types rapid follow-up messages while the tutor is generating, the Gateway pushes the message into an in-memory FIFO deque (`session_queue[session_id]`, capped at 3 messages). As soon as the active turn finishes, the orchestrator automatically pops the queued input and executes sequentially.

---

## 6. Tech stack

Every component is chosen for 100% offline local capability, deterministic execution, and low memory footprint:

| Layer | Technology | Version | Purpose / Selection Notes | License |
| :--- | :--- | :---: | :--- | :--- |
| **API Gateway** | FastAPI / Starlette | 0.115+ | High-throughput async ASGI front door, JWT auth, SSE streaming, turn locks. | MIT |
| **ASGI Web Server** | Uvicorn (standard) | 0.32+ | Async web server running Gateway and in-process math solvers. | BSD |
| **Socratic Engine** | LangGraph StateGraph | 0.2+ | Deterministic cyclic state machine for Socratic milestones, hints, and exits. | MIT |
| **Primary LLM** | Ollama / `qwen3.5:4b` | 4-bit Q4_K_M | Resident in GPU memory (3.4 GB VRAM); rephrases card templates into kid prose. | Apache 2.0 |
| **Math Solver Engine** | SymPy CAS | 1.13+ | In-process symbolic mathematics, step verification, unit equivalence. | BSD |
| **Visual Renderer** | Pure SVG / React | 18.3+ | Deterministic visual models (`ten_frame`, `base_ten_blocks`, `number_line`). | MIT |
| **Relational Database** | PostgreSQL Alpine | 16 | System of record: profiles, turn telemetry, usage ledger, unified `gap_events`. | PostgreSQL |
| **Container Engine** | Docker Compose | v2.29+ | Orchestrates 4 containers with strict CPU/RAM quotas. | Docker |

---

## 7. Math engine & Skill template library

SymPy verifies mathematical correctness (`15 + 27 = 42`), but cannot independently formulate elementary pedagogical steps (e.g. *"add the ones, trade 10 ones for 1 ten"*). ReanMore couples SymPy with a deterministic **Skill Template Library**.

### 7.1 Skill template contract

```python
# orchestrator/app/services/socratic/skills/base.py
from dataclasses import dataclass
from typing import Protocol, List, Dict, Any, Optional

@dataclass
class StepTemplate:
    goal: str                      # "Add the ones digits"
    target: str                    # "12" (held in solver memory, never in prompts)
    check_expr: str                # SymPy-evaluable AST expression
    visual_spec: Optional[Dict]    # Answer-safe VisualSpec for the student's problem
    hint_t1_nudge: str             # Gentle conceptual nudge
    hint_t2_visual: Dict           # VisualSpec using DIFFERENT numbers
    hint_t3_worked: str            # Worked example using DIFFERENT numbers

class Skill(Protocol):
    skill_id: str                  # e.g., "add_2digit_regroup"
    grade_band: str                # "grade_1_3" | "grade_4_6"
    def matches(self, problem: Dict[str, Any]) -> bool: ...
    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]: ...
    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]: ...
```

### 7.2 The 6 MVP math skills

| skill_id | Grades | Visual Model | Pedagogical Decomposition |
| :--- | :---: | :--- | :--- |
| `add_within_20` | 1-2 | `ten_frame` | Step 1: Make a ten; Step 2: Add remaining ones. |
| `sub_within_20` | 1-2 | `number_line` | Step 1: Count back to 10; Step 2: Count back remaining. |
| `add_2digit_regroup` | 2-3 | `base_ten_blocks` | Step 1: Add ones; Step 2: Trade 10 ones for 1 ten; Step 3: Add tens. |
| `sub_2digit_borrow` | 2-3 | `base_ten_blocks` | Step 1: Check ones; Step 2: Regroup 1 ten into 10 ones; Step 3: Subtract. |
| `mult_tables` | 3-4 | `array_grid` | Step 1: Identify groups and items; Step 2: Repeated addition/skip count. |
| `fraction_equivalent`| 4-5 | `fraction_bar` | Step 1: Identify denominator split; Step 2: Multiply/divide numerator. |
| `one_step_word_problem`| 1-4 | `bar_model` | Step 1: Map part-whole relationships; Step 2: Execute single operation. |

**Unmatched Problem:** If a query does not match any registered skill, the system logs a `content` gap (`NO_SKILL_MATCH`) and honestly notifies the student: *"I can't guide this kind of problem yet, but I've told my builders! 🌟"*. Zero quota charge.

---

## 8. Visual explanation generator spec

Visual models are **generated deterministically from solver data**, never by the LLM. This guarantees 100% mathematical accuracy, sub-millisecond execution, and total answer safety.

### 8.1 VisualSpec schema

```json
{
  "schema_version": 1,
  "type": "ten_frame",
  "mode": "example",
  "answer_safe": true,
  "params": {
    "frames": [{ "filled": 6 }, { "filled": 8 }],
    "color": "apple"
  },
  "highlights": [{ "from_frame": 1, "move": 4, "to_frame": 0 }],
  "labels": ["6 apples", "8 more apples"],
  "alt_text": "Two ten-frames showing 6 apples and 8 apples. Move 4 apples to make a full ten."
}
```

**Visual Modes:**
- `current`: Displays the student's **given quantities only** (operands), never the unknown target.
- `example`: Parallel problem with **strictly different numbers** (used in Tier 2/3 hints and Helpful Examples).
- `reveal`: Displays the completed solution; emitted **only** when `is_reveal_state=True`.

### 8.2 Deterministic visual leak check

Before any `VisualSpec` is serialized into `StepWidgetPayload`:
1. If `mode != "reveal"`, no parameter, counter quantity, or computed sum in the spec may equal any active or future step target.
2. If `mode == "example"`, operands must have zero intersection with the student's given numbers or targets.
3. On `number_line` in `current` mode, the landing mark is omitted.
4. On `bar_model`, the unknown quantity must render as `?`.
5. All text labels and `alt_text` strings are scanned by Leak Guard v2.

---

## 9. Data, memory, and storage

ReanMore streamlines data storage into two primary layers for the Phase 1 MVP:

| Tier | Technology | Contents | Retention Policy | Memory Budget |
| :--- | :--- | :--- | :--- | :--- |
| **Working Memory** | Python `dict` / `asyncio` | In-memory session turn locks, admission semaphore (`INFLIGHT=1`), message queue. | Sessional; cleared upon process restart. | < 256 MB RAM |
| **System of Record**| PostgreSQL 16 Alpine | Student profiles, PIN hashes, `session_logs`, `telemetry_logs`, `usage_ledger`, `gap_events`. | Permanent (minimum 5 school years). | ~5.0 GB NVMe disk |

**Workstation Memory Budget (AMD Ryzen / RTX 4050 6 GB VRAM):**

| Subsystem / Process | Host RAM | VRAM Allocation | Operational Notes |
| :--- | :---: | :---: | :--- |
| **Ollama (`qwen3.5:4b` resident)** | ~0.5 GB | **3.4 GB** (Resident) | Resident in GPU memory; fast token generation (< 2.5 s). |
| **PostgreSQL 16 Alpine** | **2.0 GB** | 0.0 GB | Shared buffers 512 MB, work_mem 32 MB. |
| **API Gateway & Orchestrator** | **1.5 GB** | 0.0 GB | FastAPI + LangGraph + in-process SymPy CAS. |
| **Frontend Web App (Nginx)** | **0.2 GB** | 0.0 GB | Serves static Vite production build. |
| **Total Containerized Stack** | **~4.2 GB** | **3.4 GB** | **Fits easily within 16 GB RAM and 6 GB VRAM.** |
| **Reserved for Host OS (Windows 11)**| **~11.8 GB** | **~2.6 GB** | Prevents host OS paging and memory thrashing. |

<a id="91-socratic-tutorstate-lifecycle-and-student-session-state"></a>

### 9.1 Socratic TutorState lifecycle and student session state

Every conversational turn is governed by `TutorState`, an atomic TypedDict persisted per turn in PostgreSQL:

```python
class TutorState(TypedDict, total=False):
    session_id: str
    user_id: str
    grade_level: str               # "grade_1_3" | "grade_4_6"
    subject: str                   # "math"
    skill_id: Optional[str]        # "add_2digit_regroup"

    # Problem Decomposition & Milestones
    problem_text: str              # Scrubbed problem text as seen by student
    total_steps_count: int         # 2 to 4 milestone steps
    current_step_index: int        # 0-indexed pointer to active milestone step
    step_widget: Optional[Dict]    # Serialized StepWidgetPayload with VisualSpec

    # Active Interaction and Progressive Hinting
    student_attempt: Optional[str] # Student's latest message or answer
    current_hint_tier: int         # 0=none, 1=nudge, 2=visual, 3=worked_example
    active_hint: Optional[str]
    attempt_history: List[Dict]

    # Frustration & Pacing
    frustration_score: float       # 0.0 to 1.0 cumulative frustration indicator
    unclear_streak: int            # Consecutive confused turns
    is_reveal_state: bool          # True only after 3 consecutive errors
```

---

## 10. Security and guardrails

### 10.1 Leak Guard v2 specification

Leak Guard v2 resolves the over-blocking issues of earlier versions while providing 100% leak defense:

1. **Given Operands Allowlist:** Numbers explicitly given in the student's problem statement (e.g. `15` and `27` in `15 + 27`) are always permitted in tutor prose.
2. **Context-Scoped Target Verification:** An expected target answer is flagged only when it appears as an isolated token (word boundaries) and is **not** inside a structural Helpful Example block.
3. **Structural Example Validation:** Worked examples emitted by `Skill.make_distinct_example()` are structurally verified to ensure none of their numbers equal the problem's operands or step targets. Once verified, the example text may use terms like "equals" freely.
4. **Narrowed Disclosure Phrase Detection:** Phrases such as *"the answer is"* or *"so it's"* are flagged only when immediately followed (within 6 tokens) by a numeric digit or number-word.
5. **Proximity Feedback Filter:** Regex barrier catches brute-force prompting clues (`off by 1`, `just one away`, `so close`, `too big`).
6. **Visual Spec Verification:** All parameter counts, counter sums, labels, and alt-texts in `VisualSpec` JSON are evaluated by the Leak Guard.
7. **Leak Quarantine & Fallback:** Any intercepted leak triggers a single retry with an explicit negative constraint; repeated violations fall back to the deterministic Skill Template hint. Every interception logs `LEAK_BLOCKED` to `gap_events`.

### 10.2 Roster-based PII scrubbing and privacy

- **Roster Deny-List:** Teachers upload the classroom student roster. Student names, nicknames, and school identifiers are compiled into an exact-match deny-list alongside standard regex filters.
- **Redacted Persistence:** Only `redacted_input` is ever committed to `telemetry_logs` and `gap_events`; raw input strings are wiped from memory.
- **Data Minimization:** Raw student telemetry is purged after **90 days**; only anonymized learning aggregates are retained.

### 10.3 PIN authentication hardening

- **Brute-Force Lockout:** Account locks for **15 minutes** after **5 consecutive failed attempts** per `(class_code, student_name)` tuple; per-IP rate limiting (10 attempts/min).
- **Argon2id Hashing:** All 4-digit student PINs are salted and hashed using `argon2id`.
- **Short-Lived JWT:** Session tokens expire after **2 hours** and are revoked upon logout.

---

## 11. Observability and Unified Gap Report

ReanMore unifies all system errors, pedagogical failures, and missing content into a single PostgreSQL table: `gap_events`.

### 11.1 Unified gap taxonomy (content, learner, system)

| Gap Type | Meaning | Actionable Fix | Example Gap Codes |
| :--- | :--- | :--- | :--- |
| **`content`** | The platform cannot teach this problem | Engineering adds skill template | `NO_SKILL_MATCH`, `UNSUPPORTED_GRADE_TOPIC`, `NO_VISUAL_FOR_SKILL` |
| **`learner`** | Student struggled with a conceptual pattern| Teacher intervenes in classroom | `MISCONCEPTION_REGROUP`, `HIGH_HINT_STEP`, `REVEAL_TRIGGERED`, `CONFUSING_FLAG` |
| **`system`** | Internal component malfunctioned | Engineering fixes bug/timeout | `LLM_TIMEOUT`, `LLM_RETRY_USED`, `TEMPLATE_FALLBACK_USED`, `LEAK_BLOCKED`, `PARSE_LOW_CONFIDENCE` |

### 11.2 PostgreSQL gap_events schema

```sql
CREATE TYPE gap_type AS ENUM ('content', 'learner', 'system');
CREATE TYPE gap_status AS ENUM ('open', 'triaged', 'fixed', 'wontfix');

CREATE TABLE gap_events (
    id              BIGSERIAL PRIMARY KEY,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    gap_type        gap_type NOT NULL,
    gap_code        VARCHAR(64) NOT NULL,
    severity        SMALLINT NOT NULL DEFAULT 2,        -- 1 low, 2 med, 3 high
    user_hash       VARCHAR(64) NOT NULL,               -- sha256(salt || user_id), never raw ID
    session_id      VARCHAR(100),
    problem_id      VARCHAR(100),
    grade_tier      VARCHAR(16),                        -- 'grade_1_3' | 'grade_4_6'
    subject         VARCHAR(16) DEFAULT 'math',
    skill_id        VARCHAR(64),
    step_index      INTEGER,
    fingerprint     VARCHAR(128) NOT NULL,              -- dedupe key: gap_code|skill_id|shape
    details         JSONB NOT NULL DEFAULT '{}'::jsonb, -- scrubbed problem, rule number, latency
    status          gap_status NOT NULL DEFAULT 'open'
);

CREATE INDEX idx_gap_events_created   ON gap_events (created_at);
CREATE INDEX idx_gap_events_type_code ON gap_events (gap_type, gap_code);
CREATE INDEX idx_gap_events_fp        ON gap_events (fingerprint);

-- Digest roll-up view
CREATE VIEW gap_summary AS
SELECT fingerprint, gap_type, gap_code, skill_id, grade_tier,
       COUNT(*)                         AS occurrences,
       COUNT(DISTINCT user_hash)        AS distinct_students,
       MIN(created_at)                  AS first_seen,
       MAX(created_at)                  AS last_seen,
       MAX(severity)                    AS max_severity
FROM gap_events
WHERE status IN ('open', 'triaged')
GROUP BY fingerprint, gap_type, gap_code, skill_id, grade_tier;
```

### 11.3 Weekly admin audit digest

Delivered every Monday at 07:00 ICT via `scripts/generate_admin_digest.py`:
1. **Executive Summary:** Total problems attempted, completion rate, % solved without Reveal, average hints per problem by grade band.
2. **Top Content Gaps:** Ranked list of unsupported problem shapes with scrubbed student examples and suggested skill templates to build.
3. **Top Learner Misconceptions:** Teacher-facing pedagogical report (e.g. *"42% of Grade 2 students failed regrouping on 2-digit addition"*).
4. **System Reliability Report:** Latency percentiles (P50/P95), LLM timeout rates, template fallback frequency, and Leak Guard interceptions by rule number.
5. **Priority Ranking Formula:**
   $$\text{Priority} = \text{Severity} \times \log_2(1 + \text{Occurrences}) \times (1 + 0.5 \times \text{Distinct Students})$$

---

## 12. Deployment and CI/CD

### 12.1 Streamlined 4-container topology

```text
Host Workstation (AMD Ryzen / Intel Core, 16 GB RAM, RTX 4050 6 GB VRAM)
 |- Ollama Server (:11434) ---> qwen3.5:4b (Resident in 3.4 GB VRAM)
 `- Docker Compose (Bridge Network: reanmore-network)
     |- reanmore-orchestrator  (:9000)  FastAPI, LangGraph, in-process SymPy, Leak Guard
     |- reanmore-postgres      (:5432)  PostgreSQL 16 Alpine (Durable System of Record)
     `- reanmore-frontend      (:3000)  React 18 / Vite / Pure SVG Stepper Web App
```

### 12.2 Container resource limits

```yaml
# Extract from backend/docker-compose.yml (MVP)
services:
  orchestrator:
    build:
      context: ./orchestrator
      dockerfile: Dockerfile
    container_name: reanmore-orchestrator
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2048M
    ports:
      - "9000:9000"
    environment:
      - OLLAMA_HOST=http://host.docker.internal:11434
      - DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/science_chatbot
      - LLM_PRIMARY_PROVIDER=ollama
      - LLM_PRIMARY_MODEL=qwen3.5:4b
      - LLM_MAX_INFLIGHT=1
      - QUOTA_DAILY=10
      - QUOTA_TZ=Asia/Phnom_Penh

  postgres:
    image: postgres:16-alpine
    container_name: reanmore-postgres
    deploy:
      resources:
        limits:
          cpus: '1.5'
          memory: 2048M
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=science_chatbot

  frontend:
    build:
      context: ../frontend
      dockerfile: Dockerfile
    container_name: reanmore-frontend
    ports:
      - "3000:80"
    depends_on:
      - orchestrator
```

---

## 13. Repository layout

Streamlined layout reflecting the Phase 1 MVP architecture:

```text
reanmore/
|-- backend/
|   |-- docker-compose.yml              # 4-container streamlined MVP topology
|   |-- requirements.txt
|   |-- pytest.ini
|   |-- README.md
|   |-- orchestrator/
|   |   |-- Dockerfile
|   |   |-- requirements.txt
|   |   \-- app/
|   |       |-- main.py
|   |       |-- api/
|   |       |   |-- endpoints.py        # /query, /step/navigate, /auth
|   |       |   \-- health_routes.py
|   |       |-- core/
|   |       |   |-- config.py
|   |       |   \-- logging.py
|   |       |-- infrastructure/
|   |       |   |-- database.py         # Async PostgreSQL engine, ORM models
|   |       |   \-- metrics.py
|   |       \-- services/
|   |           |-- auth/
|   |           |   |-- security.py     # Argon2id PIN hashing & lockout logic
|   |           |   \-- pin_service.py
|   |           |-- guardrails/
|   |           |   |-- pii_scrubber.py # Roster-based deny list + regex
|   |           |   |-- safety_filter.py
|   |           |   |-- educational_scope.py
|   |           |   \-- leak_guard.py   # Leak Guard v2 engine
|   |           |-- llm/
|   |           |   |-- base.py
|   |           |   |-- manager.py      # Semaphore admission (INFLIGHT=1)
|   |           |   |-- providers/
|   |           |   |   \-- ollama_provider.py
|   |           |   \-- optional_cloud/ # Optional Gemini/OpenAI (disabled by default)
|   |           |-- quota/
|   |           |   |-- quota_guard.py  # Daily PostgreSQL quota enforcer
|   |           |   \-- usage_ledger_repo.py
|   |           |-- visuals/            # Deterministic SVG VisualSpec builders
|   |           |   |-- base.py
|   |           |   |-- ten_frame.py
|   |           |   |-- number_line.py
|   |           |   |-- base_ten_blocks.py
|   |           |   \-- fraction_bar.py
|   |           \-- socratic/
|   |               |-- state.py        # TutorState TypedDict
|   |               |-- card_schema.py  # StepWidgetPayload schema
|   |               |-- graph.py        # LangGraph StateGraph
|   |               |-- parse_verifier.py # Word problem parse verification
|   |               |-- hint_engine.py
|   |               |-- reveal_and_continue.py
|   |               |-- skills/         # 6 core math skill templates
|   |               |   |-- base.py
|   |               |   |-- add_within_20.py
|   |               |   |-- add_2digit_regroup.py
|   |               |   \-- fraction_equivalent.py
|   |               \-- prompts/
|   \-- testing/
|       |-- conftest.py
|       |-- data/
|       |   |-- golden_50_math_worksheets.jsonl
|       |   \-- adversarial_100_leak_cases.jsonl
|       |-- bench_concurrency.py        # Multi-student concurrent load benchmark
|       \-- unit/
|           |-- adversarial_evaluator.py
|           |-- test_visual_specs.py
|           |-- test_parse_verifier.py
|           \-- test_quota_guard.py
|-- frontend/
|   |-- Dockerfile
|   |-- package.json
|   |-- vite.config.ts
|   \-- src/
|       |-- App.tsx
|       |-- components/
|       |   |-- StepperWidget.tsx
|       |   |-- SocraticCard.tsx
|       |   |-- VisualRenderer.tsx      # Pure SVG visual model renderer
|       |   |-- MathKeyboard.tsx        # Kid-friendly math input / tap-to-build
|       |   \-- QuotaPill.tsx
|       \-- types/
|           \-- visual.ts               # VisualSpec TypeScript types
\-- docs/
    |-- ReanMore_Architecture_v2.1.md
    |-- ReanMore_Change_Pack.md
    \-- stepper_widget_specification.md
```

---

## 14. Risks, open questions & decision log

**Architectural risks and mitigations:**

| Risk | What Could Happen | Technical Mitigation Mechanism |
| :--- | :--- | :--- |
| **LLM gives the answer away directly** | Student copies answer without learning. | Isolated ground-truth state + Leak Guard v2 multi-rule scanner. |
| **LLM solves wrong word problem** | Student guided to a perfectly calculated wrong answer. | 7-stage parse verification pipeline + free child confirmation prompt. |
| **VRAM exhaustion crashes Ollama** | Workstation runs out of memory on concurrent turns. | Bounded semaphore (`INFLIGHT=1`); single resident model; template fallback. |
| **Visual model reveals answer** | Diagram displays the computed sum before child solves it. | Deterministic Visual Leak Check; mode-restricted SVG specs. |
| **Brute-force PIN guessing** | Unauthorized student accesses peer account. | Argon2id hashing; account lockout after 5 failed attempts; IP rate limits. |
| **Runaway token generation hangs GPU**| LLM generates endless text on confusing inputs. | Strict first-token timeout (6.0 s) + `num_predict: 220` token ceiling. |

**Decision log:**

| Date | Architectural Decision | Rationale / Trade-offs |
| :--- | :--- | :--- |
| **2026-10-14** | LangGraph StateGraph over plain LCEL chains | Cyclic graph required for 3-tier hints, retries, and Reveal & Continue. |
| **2026-10-14** | SymPy CAS for Math Engine | Guarantees 100% symbolic and arithmetic accuracy. |
| **2026-10-16** | English-first v2.1 MVP; Khmer deferred to v2.2 | Accelerates stable MVP launch; avoids unspaced Khmer script errors. |
| **2026-10-16** | Local Ollama as Primary LLM (`qwen3.5:4b`) | 100% offline execution; zero cloud API cost; student privacy. |
| **2026-10-19** | **Thin Vertical Slice (Scope Cut)** | Pruned Redis, MinIO, Qdrant, and photo OCR for Phase 1; focus strictly on Math. |
| **2026-10-19** | **Single-Model Fallback Ladder** | Eliminated multi-model swapping; resident model retries once, then uses Skill Templates. |
| **2026-10-19** | **Deterministic SVG VisualSpec** | Visuals generated by Python math builders, not LLM; rendered via pure SVG. |
| **2026-10-19** | **Leak Guard v2** | Added operand allowlist, 6-token disclosure window, and visual spec inspections. |
| **2026-10-19** | **Unified Gap Accounting (`gap_events`)** | Single PostgreSQL table tracking content, learner, and system gaps for weekly digests. |
| **2026-10-19** | **PostgreSQL-Only Quota & State** | Eliminated Redis dependency for MVP; daily quota and turn state handled in Postgres. |

---

## 15. Phased roadmap & evaluation with real kids

### 15.1 Phased execution roadmap

| Phase | Focus & Deliverables | Exit Criteria |
| :--- | :--- | :--- |
| **Phase 0: Benchmarks** | Measure exact `qwen3.5:4b` latency, VRAM peak, and concurrency under `LLM_MAX_INFLIGHT = 1`. | Benchmark table filled with measured workstation data. |
| **Phase 1: Math Vertical Slice** | Typed math input, 6 skill templates, template steps, Leak Guard v2, 6 SVG visual models, PostgreSQL, `gap_events`. | All unit tests pass; 0 leaks on release benchmark suite; teacher reviews 50 hints. |
| **Phase 2: Real-Kid Pilot** | 6-10 students (Grades 1-3 & 4-6) in 20-min guided homework sessions with consent. | Comprehension check & transfer check completed; gap report reviewed. |
| **Phase 3: Curriculum Science RAG**| Add Qdrant vector DB & BGE reranker; index English primary science textbooks; curriculum gap logging. | RAGAS Faithfulness >= 0.95 on science test set. |
| **Phase 4: Worksheet Photo Ingress**| Add IBM Docling v2 & MinIO file vault; clean printed worksheet upload with child confirmation prompt. | OCR accuracy measured on classroom worksheet samples. |
| **Phase 5: Distributed Scale & Khmer**| Add Redis Streams, multi-node clustering, and Khmer script normalizer (v2.2). | Validated against school lab multi-node requirements. |

### 15.2 Real-kid pilot evaluation protocol

1. **Cohort & Setting:** 6-10 students (3-5 from Grades 1-3, 3-5 from Grades 4-6). Conducted with parental/school consent in the presence of a classroom teacher.
2. **Session Format:** 20-minute sessions per student; 3-5 problems matched to current classroom topics. Observers record interactions without intervening unless the child is completely stuck.
3. **Core Observational Metrics:**
   - Problem completion rate (% solved without quitting).
   - Average hint tier utilized per problem.
   - Reveal & Continue trigger rate (target: < 15%).
   - Visual model engagement (did the child view/interact with the SVG diagram?).
   - **Comprehension Check:** At problem completion, the observer asks: *"Can you explain to me how you got that?"*
   - **Transfer Check:** Child is presented with an isomorphic follow-up problem without tutor hints to verify independent mastery.
4. **Readability Gate:**
   - Sentence length strictly capped: Grades 1-3 <= 12 words; Grades 4-6 <= 18 words.
   - Post-generation readability scan enforces grade-appropriate vocabulary; failures automatically trigger template text fallback.

---

<a id="appendices"></a>

## Appendices

- [Appendix A. Detailed protocol diagram](#appendix-a-detailed-protocol-diagram)
- [Appendix B. Storage tiers & Repository interfaces](#appendix-b-storage-tiers--repository-interfaces)
- [Appendix C. Skill templates & parse verification code](#appendix-c-skill-templates--parse-verification-code)
- [Appendix D. Dynamic prompt engine & Socratic card templates](#appendix-d-dynamic-prompt-engine--socratic-card-templates)
- [Appendix E. Local runtime implementation and concurrency control](#appendix-e-local-runtime-implementation-and-concurrency-control)
- [Appendix F. Model router configuration](#appendix-f-model-router-configuration)
- [Appendix G. Cost and hardware budget breakdown](#appendix-g-cost-and-hardware-budget-breakdown)
- [Appendix H. Leak Guard v2 engine & test harness](#appendix-h-leak-guard-v2-engine--test-harness)
- [Appendix I. Full repository tree](#appendix-i-full-repository-tree)

---

<a id="appendix-a-detailed-protocol-diagram"></a>

## Appendix A. Detailed protocol diagram

```text
                           STUDENTS & CLASSROOM TEACHERS
                      (Grades 1-6 Elementary School Students)
                                        |
                                        v
                            ReanMore Stepper Web UI
                  (React 18 / Vite / Pure SVG Stepper Widget)
                                        | (HTTPS / SSE Connection)
                                        v
                    +---------------------------------------+
                    | FastAPI Gateway & Ingress Router      |
                    | (:9000)                               |
                    |                                       |
                    | - Class Code + PIN Auth Claim         |
                    | - In-Memory Session Turn Lock         |
                    | - Admission Semaphore (INFLIGHT=1)    |
                    | - Daily Quota Guard (10 problems/day) |
                    | - Latency: < 10ms                     |
                    +---------------------------------------+
                                        |
                                        v
                    +---------------------------------------+
                    | Tier 1A Deterministic Pre-Filter      |
                    | (Front-Door Security Barrier)         |
                    |                                       |
                    | - Roster Deny-List & Regex PII Scrubber
                    | - Injection & Delimiter Sanitizer     |
                    | - English Typography Normalization    |
                    | - Math Operator Preservation          |
                    | - Latency: < 10ms                     |
                    +---------------------------------------+
                                        |
                 +----------------------+----------------------+
                 |                                             |
   [Smalltalk / Greeting / Ping]                   [Math Homework Inquiry / Validated]
                 |                                             |
                 v                                             v
  +-----------------------------+              +-------------------------------+
  | Static Short-Circuit Engine |              | Word Problem Parse Verifier   |
  | - Instant Friendly Greeting |              | - Operand Existence & Coverage|
  | - Zero LLM Calls            |              | - Operator Sanity Check       |
  | - Latency: < 50ms total     |              | - Free Child Confirm Prompt   |
  +-----------------------------+              +-------------------------------+
                 |                                             |
                 |                                             v
                 |                             +-------------------------------+
                 |                             | Socratic Skill Dispatcher     |
                 |                             | (`orchestrator/socratic/`)    |
                 |                             |                               |
                 |                             | - Matches 1 of 6 Math Skills  |
                 |                             | - Builds 2-4 Verified Steps   |
                 |                             | - Generates Answer-Safe       |
                 |                             |   VisualSpec JSON             |
                 |                             +-------------------------------+
                 |                                             |
                 |                                             v
                 |                             +-------------------------------+
                 |                             | Local Ollama Single-Model Loop|
                 |                             | (:11434, qwen3.5:4b Resident) |
                 |                             |                               |
                 |                             | - Rephrases Template to Prose |
                 |                             | - First-Token Timeout: 6.0s   |
                 |                             | - Retry Once on Failure       |
                 |                             | - Fallback: Skill Template    |
                 |                             +-------------------------------+
                 |                                             |
                 |                                             v
                 |                             +-------------------------------+
                 |                             | Leak Guard v2 Engine          |
                 |                             | (`leak_guard.py`)             |
                 |                             |                               |
                 |                             | - Given Operands Allowlist    |
                 |                             | - Scoped Target Check         |
                 |                             | - Structural Example Check    |
                 |                             | - 6-Token Disclosure Window   |
                 |                             | - VisualSpec Parameter Check  |
                 |                             +-------------------------------+
                 |                                             |
                 +------------------------+--------------------+
                                          |
                                          v
                 +-------------------------------------------------------------+
                 | Quota Commit & Dual-Payload Serialization                   |
                 | - Commit Problem Deduction to PostgreSQL `usage_ledger`     |
                 | - Record Any Gap Events to PostgreSQL `gap_events`          |
                 | - Serialize `StepWidgetPayload` (with VisualSpec) + Markdown|
                 | - Checkpoint `TutorState` in PostgreSQL                     |
                 | - Release Turn Lock & In-Memory Admission Semaphore         |
                 +------------------------------+------------------------------+
                                                |
                                                v
                               Real-Time Streaming SSE Response
                      (Client reconnects anytime; fetches state from DB)
```

---

<a id="appendix-b-storage-tiers--repository-interfaces"></a>

## Appendix B. Storage tiers & Repository interfaces

### LocalVaultStorageAdapter implementation

```python
# backend/orchestrator/app/infrastructure/storage_adapter.py
from abc import ABC, abstractmethod
from pathlib import Path

class StorageProvider(ABC):
    @abstractmethod
    async def save_document(self, file_bytes: bytes, destination_path: str) -> str:
        """Stores an uploaded curriculum document or scan and returns its vault path."""
        pass

    @abstractmethod
    async def retrieve_document(self, vault_path: str) -> bytes:
        """Retrieves raw document bytes for parsing or verification."""
        pass

class LocalVaultStorageAdapter(StorageProvider):
    def __init__(self, base_dir: str = "./data/vault"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    async def save_document(self, file_bytes: bytes, destination_path: str) -> str:
        target_path = self.base_dir / destination_path
        target_path.parent.mkdir(parents=True, exist_ok=True)
        target_path.write_bytes(file_bytes)
        return str(target_path)

    async def retrieve_document(self, vault_path: str) -> bytes:
        target = Path(vault_path)
        if not target.exists():
            raise FileNotFoundError(f"Vault document not found: {vault_path}")
        return target.read_bytes()
```

### UsageLedgerRepo durable daily quota implementation

```python
# backend/orchestrator/app/services/quota/usage_ledger_repo.py
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.exc import IntegrityError
import zoneinfo

from app.infrastructure.database import UsageLedger, AsyncSessionLocal

logger = logging.getLogger("reanmore.quota.ledger")

class UsageLedgerRepo:
    """
    Durable PostgreSQL ledger repository for student daily problem quotas.
    Guarantees zero double-counting via UniqueConstraint(user_id, problem_id).
    """
    async def get_daily_usage_count(self, user_id: str, tz_name: str = "Asia/Phnom_Penh") -> int:
        tz = zoneinfo.ZoneInfo(tz_name)
        now_local = datetime.now(tz)
        start_of_day = datetime(now_local.year, now_local.month, now_local.day, 0, 0, 0, tzinfo=tz)

        async with AsyncSessionLocal() as session:
            stmt = select(func.count(UsageLedger.id)).where(
                UsageLedger.user_id == user_id,
                UsageLedger.created_at >= start_of_day
            )
            res = await session.execute(stmt)
            return res.scalar() or 0

    async def record_quota_transaction(
        self,
        user_id: str,
        problem_id: str,
        problem_hash: Optional[str] = None,
        subject: str = "math"
    ) -> bool:
        async with AsyncSessionLocal() as session:
            try:
                async with session.begin():
                    record = UsageLedger(
                        user_id=user_id,
                        problem_id=problem_id,
                        problem_hash=problem_hash,
                        subject=subject,
                        created_at=datetime.utcnow()
                    )
                    session.add(record)
                return True
            except IntegrityError:
                logger.warning(f"Quota Ledger: Duplicate problem transaction for user={user_id}, problem={problem_id}")
                return False
```

---

<a id="appendix-c-skill-templates--parse-verification-code"></a>

## Appendix C. Skill templates & parse verification code

```python
# backend/orchestrator/app/services/socratic/skills/add_2digit_regroup.py
from typing import Dict, Any, List
from app.services.socratic.skills.base import Skill, StepTemplate

class Add2DigitRegroupSkill(Skill):
    skill_id = "add_2digit_regroup"
    grade_band = "grade_1_3"

    def matches(self, problem: Dict[str, Any]) -> bool:
        op = problem.get("operation")
        operands = problem.get("operands", [])
        if op == "add" and len(operands) == 2:
            a, b = operands
            if 10 <= a <= 99 and 10 <= b <= 99:
                return ((a % 10) + (b % 10)) >= 10
        return False

    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]:
        a, b = problem["operands"]
        ones_sum = (a % 10) + (b % 10)
        tens_sum = (a // 10) + (b // 10) + (1 if ones_sum >= 10 else 0)

        step1 = StepTemplate(
            goal="Add the ones digits together",
            target=str(ones_sum),
            check_expr=f"{a % 10} + {b % 10}",
            visual_spec={
                "type": "base_ten_blocks",
                "mode": "current",
                "params": {"a": a, "b": b, "focus": "ones"}
            },
            hint_t1_nudge="Look only at the numbers in the ones column on the far right.",
            hint_t2_visual={
                "type": "ten_frame",
                "mode": "example",
                "params": {"frames": [{"filled": 6}, {"filled": 7}]}
            },
            hint_t3_worked="In 14 + 18, we add 4 + 8 to get 12 ones. What is our ones sum?"
        )
        return [step1]
```

---

<a id="appendix-d-dynamic-prompt-engine--socratic-card-templates"></a>

## Appendix D. Dynamic prompt engine & Socratic card templates

```text
orchestrator/app/services/socratic/prompts/
|-- parse_word_problem.jinja2     # Extracts structured operands and units from text
|-- rephrase_step_card.jinja2     # Injects kid-friendly warmth into deterministic templates
|-- hint_nudge.jinja2             # Gentle conceptual question prompt
\-- validation_retry.jinja2       # Leak-free correction prompt when Leak Guard intercepts
```

### The 4-Part Socratic Step Card specification

1. 🌟 **Our Mission:** Exactly one motivating sentence defining the active milestone goal.
2. 💡 **Clue:** Grade-appropriate rule or property (contains zero answers).
3. 🍎 **Helpful Example:** An isomorphic parallel example with visual emojis, strictly utilizing **different numbers** from the student's problem.
4. 👉 **Your Turn:** Exactly **one single question** prompting the student to execute the active step.

---

<a id="appendix-e-local-runtime-implementation-and-concurrency-control"></a>

## Appendix E. Local runtime implementation and concurrency control

```python
# backend/orchestrator/app/services/llm/manager.py
import asyncio
import httpx
from typing import Optional, Dict, Any
from app.core.config import settings

class LLMManager:
    """
    Admission-controlled single-model LLM manager running over Ollama.
    Enforces LLM_MAX_INFLIGHT=1 and first-token streaming deadlines.
    """
    def __init__(self):
        self.semaphore = asyncio.Semaphore(getattr(settings, "LLM_MAX_INFLIGHT", 1))
        self.endpoint = getattr(settings, "OLLAMA_HOST", "http://localhost:11434")
        self.model = getattr(settings, "LLM_PRIMARY_MODEL", "qwen3.5:4b")

    async def generate_step_card(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        async with self.semaphore:
            # Rung 1: Primary streaming attempt
            result = await self._call_ollama(system_prompt, user_prompt)
            if result:
                return result

            # Rung 2: Single retry on resident model
            return await self._call_ollama(system_prompt, user_prompt)

    async def _call_ollama(self, system_prompt: str, user_prompt: str) -> Optional[str]:
        timeout = httpx.Timeout(connect=2.0, read=6.0, write=5.0, pool=2.0)
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    f"{self.endpoint}/api/chat",
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        "options": {
                            "temperature": 0.2,
                            "num_predict": 220,  # Max output tokens ceiling
                            "seed": 42
                        }
                    }
                )
                if resp.status_code == 200:
                    return resp.json()["message"]["content"]
        except Exception:
            return None
        return None
```

---

<a id="appendix-f-model-router-configuration"></a>

## Appendix F. Model router configuration

```yaml
# config/model_routing.yaml
model_routing:
  default_provider: "ollama"
  timeout_seconds: 15.0
  first_token_timeout_seconds: 6.0
  max_inflight_semaphore: 1
  max_output_tokens: 220

  models:
    primary:
      name: "qwen3.5:4b"
      format: "ollama"
      resident: true
      quantization: "Q4_K_M"

  fallback_ladder:
    rung_1: "primary_model"
    rung_2: "single_retry_same_model"
    rung_3: "skill_template_fallback"
    rung_4: "honest_degraded_notice"
```

---

<a id="appendix-g-cost-and-hardware-budget-breakdown"></a>

## Appendix G. Cost and hardware budget breakdown

Because ReanMore operates 100% offline via local Ollama inference without cloud API dependencies, variable per-query inference costs are exactly $0.00:

| Infrastructure Item | Technology / Hardware | Operational Allocation | Marginal Cost per Turn | Monthly Cost | Licensing |
| :--- | :--- | :--- | :---: | :---: | :--- |
| **Compute Workstation** | AMD Ryzen / Intel Core | 8 Cores (host workstation) | $0.00 | $0.00 | Owned |
| **GPU Accelerator** | NVIDIA RTX 4050 Laptop | 6.0 GB VRAM (3.4 GB allocated) | $0.00 | $0.00 | Owned |
| **Host Operating System**| Windows 11 / Linux | Host platform | $0.00 | $0.00 | Licensed |
| **Primary LLM** | Ollama (`qwen3.5:4b`) | Local GPU/CPU execution | $0.00 | $0.00 | Open Source / Apache 2.0 |
| **Math Engine** | SymPy CAS | In-process Python module | $0.00 | $0.00 | Open Source / BSD |
| **Relational Database** | PostgreSQL 16 Alpine | 2.0 GB RAM container cap | $0.00 | $0.00 | Open Source / PostgreSQL |
| **Frontend Web App** | React 18 / Vite / Nginx | 0.2 GB RAM container cap | $0.00 | $0.00 | Open Source / MIT |
| **Total Platform Stack** | **100% Local (4 Containers)**| **~4.2 GB RAM / 3.4 GB VRAM** | **$0.0000** | **$0.00** | **Zero Variable Cost** |

---

<a id="appendix-h-leak-guard-v2-engine--test-harness"></a>

## Appendix H. Leak Guard v2 engine & test harness

```python
# backend/orchestrator/app/services/guardrails/leak_guard.py
import re
from typing import Optional, List, Dict, Any, Set
from dataclasses import dataclass

@dataclass
class LeakCheckResult:
    is_clean: bool
    detected_leak: Optional[str] = None
    rule_triggered: Optional[int] = None

class LeakGuardV2:
    def inspect(
        self,
        text: str,
        given_operands: Set[str],
        target_answer: str,
        visual_spec: Optional[Dict] = None,
        is_reveal_state: bool = False
    ) -> LeakCheckResult:
        if is_reveal_state:
            return LeakCheckResult(is_clean=True)

        # Rule 1 & Allowlist: Given operands are exempt; target is blocked if isolated token
        normalized_text = text.lower()
        target_tokens = [target_answer.lower()]

        for target in target_tokens:
            if target in given_operands:
                continue
            pattern = rf"\b{re.escape(target)}\b"
            if re.search(pattern, normalized_text):
                return LeakCheckResult(is_clean=False, detected_leak=target, rule_triggered=1)

        # Rule 4: Narrowed 6-token disclosure phrase window
        phrase_re = re.compile(r"\b(?:the answer is|so it's|equals|is equal to)\s+(\w+)", re.IGNORECASE)
        match = phrase_re.search(text)
        if match:
            captured_val = match.group(1).lower()
            if captured_val == target_answer.lower() and captured_val not in given_operands:
                return LeakCheckResult(is_clean=False, detected_leak=captured_val, rule_triggered=4)

        # Rule 5: Proximity encouragement regex
        proximity_re = re.compile(r"\b(?:off by \d+|just one (?:more|less|away)|so close)\b", re.IGNORECASE)
        if proximity_re.search(text):
            return LeakCheckResult(is_clean=False, detected_leak="proximity_clue", rule_triggered=5)

        return LeakCheckResult(is_clean=True)
```

---

<a id="appendix-i-full-repository-tree"></a>

## Appendix I. Full repository tree

```text
reanmore/
|-- .agents/
|   \-- skills/
|       |-- architecture-auditor/
|       |   \-- SKILL.md
|       |-- backend-master/
|       |   \-- SKILL.md
|       |-- change-control/
|       |   \-- SKILL.md
|       |-- langchain-agent-builder/
|       |   \-- SKILL.md
|       |-- no-mock-guardian/
|       |   \-- SKILL.md
|       |-- observability/
|       |   \-- SKILL.md
|       |-- prompt-engineer/
|       |   \-- SKILL.md
|       |-- quota-system/
|       |   \-- SKILL.md
|       |-- release-gate/
|       |   \-- SKILL.md
|       |-- safety-and-guardrails/
|       |   \-- SKILL.md
|       \-- tutor-pedagogy/
|           \-- SKILL.md
|-- backend/
|   |-- docker-compose.yml              # Streamlined 4-container topology
|   |-- requirements.txt
|   |-- pytest.ini
|   |-- README.md
|   |-- orchestrator/
|   |   |-- Dockerfile
|   |   |-- requirements.txt
|   |   \-- app/
|   |       |-- main.py
|   |       |-- api/
|   |       |   |-- endpoints.py        # /query, /step/navigate, /auth
|   |       |   \-- health_routes.py
|   |       |-- core/
|   |       |   |-- config.py
|   |       |   \-- logging.py
|   |       |-- infrastructure/
|   |       |   |-- database.py         # PostgreSQL engine & gap_events schema
|   |       |   |-- storage_adapter.py  # LocalVaultStorageAdapter
|   |       |   \-- metrics.py
|   |       \-- services/
|   |           |-- auth/
|   |           |   |-- security.py     # Argon2id PIN hashing & lockout logic
|   |           |   \-- pin_service.py
|   |           |-- guardrails/
|   |           |   |-- pii_scrubber.py # Roster-based deny-list + regex
|   |           |   |-- safety_filter.py
|   |           |   |-- educational_scope.py
|   |           |   \-- leak_guard.py   # Leak Guard v2 engine
|   |           |-- llm/
|   |           |   |-- base.py
|   |           |   |-- manager.py      # Bounded semaphore (LLM_MAX_INFLIGHT=1)
|   |           |   |-- providers/
|   |           |   |   \-- ollama_provider.py
|   |           |   \-- optional_cloud/ # Optional cloud adapters (disabled by default)
|   |           |-- quota/
|   |           |   |-- quota_guard.py  # Daily PostgreSQL quota enforcer
|   |           |   \-- usage_ledger_repo.py
|   |           |-- visuals/            # Deterministic SVG VisualSpec builders
|   |           |   |-- base.py
|   |           |   |-- ten_frame.py
|   |           |   |-- number_line.py
|   |           |   |-- base_ten_blocks.py
|   |           |   \-- fraction_bar.py
|   |           \-- socratic/
|   |               |-- state.py        # TutorState TypedDict
|   |               |-- card_schema.py  # StepWidgetPayload schema
|   |               |-- graph.py        # LangGraph StateGraph
|   |               |-- parse_verifier.py # Word problem parse verification
|   |               |-- hint_engine.py
|   |               |-- reveal_and_continue.py
|   |               |-- skills/         # 6 core math skill templates
|   |               |   |-- base.py
|   |               |   |-- add_within_20.py
|   |               |   |-- add_2digit_regroup.py
|   |               |   |-- sub_2digit_borrow.py
|   |               |   |-- mult_tables.py
|   |               |   |-- fraction_equivalent.py
|   |               |   \-- one_step_word_problem.py
|   |               \-- prompts/
|   \-- testing/
|       |-- conftest.py
|       |-- data/
|       |   |-- golden_50_math_worksheets.jsonl
|       |   \-- adversarial_100_leak_cases.jsonl
|       |-- bench_concurrency.py        # Multi-student concurrent load benchmark
|       \-- unit/
|           |-- adversarial_evaluator.py
|           |-- test_visual_specs.py
|           |-- test_parse_verifier.py
|           \-- test_quota_guard.py
|-- frontend/
|   |-- Dockerfile
|   |-- package.json
|   |-- vite.config.ts
|   |-- index.html
|   |-- nginx.conf
|   \-- src/
|       |-- App.tsx
|       |-- components/
|       |   |-- StepperWidget.tsx
|       |   |-- SocraticCard.tsx
|       |   |-- VisualRenderer.tsx      # Pure SVG visual model renderer
|       |   |-- MathKeyboard.tsx        # Kid-friendly math input / tap-to-build
|       |   \-- QuotaPill.tsx
|       \-- types/
|           |-- visual.ts               # VisualSpec TypeScript types
|           \-- stepper.ts
\-- docs/
    |-- ReanMore_Architecture_v2.1.md
    |-- ReanMore_Change_Pack.md
    \-- stepper_widget_specification.md
```
