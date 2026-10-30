# ReanMore.ai (រៀនបន្ថែម) 🚀

> **Agentic Socratic STEM Homework Tutor for Elementary Students (Grades 1–6)**  
> Engineered for 100% offline execution ($0.00 cloud API cost), zero direct answer leaks, deterministic SVG visual models, and pedagogical Socratic scaffolding for Mathematics.  
> *Aligned with the Khmer Enterprise (KE) & Ministry of Education, Youth and Sport (MoEYS) STEM Initiative.*

---

## 🌟 Executive Overview

**ReanMore.ai** is an agentic AI tutoring platform built specifically for young learners (ages 6–12). While generic chatbots give away answers and encourage passive copying, ReanMore acts as an encouraging, pedagogical Socratic guide:

- **Strict Socratic Decomposition:** Breaks problems into 1–4 purposeful milestones (Mission, Clue, Helpful Example, Your Turn): one real step for direct facts, 2–4 for strategy-driven problems. It never asks the child to re-transcribe numbers already on screen.
- **Relatable Concrete Analogies:** Replaces dry academic jargon with warm, memorable kid stories (*"Cookie Bakery Boxes"*, *"Tall Ten-Towers"*, *"Crayon Box Sharing"*, and *"Apple Baskets"*).
- **100% Offline & Private:** Sized specifically to run on a single local laptop or classroom workstation (AMD Ryzen / Intel Core i7, 16 GB RAM, RTX 4050 6 GB VRAM or CPU).
- **Zero Cloud API Costs:** Powered by a local resident Ollama instance (`qwen3.5:4b`, 3.4 GB VRAM) paired with an in-process SymPy Computer Algebra System (CAS).
- **Leak Guard v2:** Mathematically and syntactically intercepts and blocks outgoing prose or visual labels containing target answers before they reach the child.

---

## 🏗️ Actual System Architecture (v2.1 Thin Vertical Slice)

In accordance with **[Architecture Specification v2.1](docs/ReanMore_Architecture_v2.1.md)**, ReanMore refactors legacy multi-container complexity into a **streamlined 4-container topology** optimized for single-machine stability and zero VRAM exhaustion:

```text
               Grades 1-6 Students | Classroom Teachers | Parents | Admins
                                          │
                         React 19 Stepper UI / Mobile Web PWA
                                          │ (Port 5173 / 3000 · REST & SSE)
                                          ▼
+===================================================================================+
| API Gateway & Socratic Orchestrator (FastAPI :9000)                                |
| ├── Class Code + 4-digit PIN Authentication (argon2id, lockout after 5 fails)     |
| ├── In-Memory Turn Lock (`asyncio.Lock`) & Bounded Semaphore (`LLM_MAX_INFLIGHT=1`)|
| ├── Two-Phase Quota Guard (10 problems/day ledger in Asia/Phnom_Penh, UTC+7)     |
| └── Server-Sent Events (SSE) Stream Dispatcher with Session Rehydration           |
+----------------------------------------+------------------------------------------+
                                         │
                                         ▼
+===================================================================================+
| Deterministic Ingress Pre-Filter (< 10 ms, zero LLM calls)                        |
| ├── Roster-Based & Regex PII Scrubber (Masks Student Names, Phones, Locations)    |
| ├── Math Notation Sanitizer (Preserves +, -, *, /, ^, =)                          |
| └── Intent & Scope Gate: Deflects off-topic chats; greetings short-circuit (<50ms)|
+----------------------------------------+------------------------------------------+
                                         │
                                         ▼ (Checkpoints & Rehydrates TutorState)
+===================================================================================+
| Socratic LangGraph StateGraph (`orchestrator/app/services/socratic/`)             |
| ├── Word Problem Parse Verifier: 7-stage deterministic operand & keyword check   |
| ├── Math Skill Registry: 6 core deterministic elementary skills (AST verification)|
| ├── 3-Tier Progressive Hint Engine: Nudge ➔ VisualSpec ➔ Worked Example           |
| └── Reveal & Continue: Pedagogical exit node after 3 failed student attempts      |
+-------------------+-------------------------------------------+-------------------+
                    │                                           │
                    ▼                                           ▼
+---------------------------------------+   +---------------------------------------+
| In-Process Math Engine (SymPy CAS)    |   | Visual Explanation Spec Generator    |
| ├── Exact Symbolic Arithmetic Check   |   | ├── Pure Deterministic VisualSpec JSON|
| ├── Algebraic AST Equivalence Checking|   | ├── 6 SVG Models (Ten-Frame, Bar, etc)|
| └── Target Answers Isolated in Memory |   | └── Answer-Safe Mode Isolation        |
+-------------------+-------------------+   +-------------------+-------------------+
                    │                                           │
                    +---------------------+---------------------+
                                          │
                                          ▼
+===================================================================================+
| Local Single-Model LLM Runtime (Ollama Server :11434, `qwen3.5:4b` Resident)      |
| ├── Rephrases pedagogical card templates into encouraging, age-appropriate prose  |
| ├── Latency Target: First-token < 6.0 s | Max Output: 220 tokens (`num_predict`)   |
| ├── 4-Rung Failover: Resident Call ➔ Single Retry ➔ Skill Template ➔ Rest Notice  |
| └── $0.00 Marginal Inference Cost; 100% Workstation Local & Zero Cloud Dependency |
+-----------------------------------------+-----------------------------------------+
                                          │
                                          ▼
+===================================================================================+
| Leak Guard v2 (`leak_guard.py`)                                                   |
| ├── Scans outgoing prose AND VisualSpec labels for target values & leak phrases   |
| ├── Operand Allowlist: Student problem's given numbers are exempt from blocking   |
| ├── Word-to-Number Mapping: English words ("twelve" ➔ 12, "half" ➔ 1/2)          |
| └── Blocked leaks trigger deterministic Skill Template fallback (< 15 ms)         |
+-----------------------------------------+-----------------------------------------+
                                          │
                                          ▼
+===================================================================================+
| System of Record: PostgreSQL 16 Alpine (:5432)                                    |
| ├── Student Profiles & PIN Credentials                                            |
| ├── Session Turn History & Telemetry Traces (`telemetry_logs`)                    |
| ├── Problem Usage Ledger (`usage_ledger` - 10 problems/day reset at 00:00 ICT)   |
| └── Unified Gap Accounting (`gap_events`: Content, Learner, and System gaps)      |
+===================================================================================+
```

> **Note on Distributed Services:** Multi-container distributed storage (Redis Streams, Qdrant Vector DB, MinIO Object Storage) are maintained in `backend/docker-compose.full.yml` for future distributed deployments. The Phase 1 MVP intentionally operates on the streamlined 4-container stack to guarantee sub-second startup and rock-solid demo reliability.

---

## 🚀 Key Architectural Pillars

### 1. 🛡️ Leak Guard v2 (The Socratic Invariant)
The core pedagogical invariant is that **the tutor never reveals the final answer prematurely**.
- Target values are computed by the in-process CAS engine and kept in isolated memory.
- All LLM-generated output passes through `Leak Guard v2`, which evaluates:
  1. **Direct Value Leakage:** Exact string matches of final numbers or fractions.
  2. **Word-to-Number Transliterations:** English words (e.g. *"forty-two"*, *"twelve"*).
  3. **Roundabout Leak Phrases:** 6-token sliding window detecting disclosure clauses (e.g. *"the answer is"*, *"equals to"*).
  4. **Operand Allowlist:** Numbers given in the student's original problem (e.g., 15 and 27 in "15 + 27") are allowlisted so the tutor can freely reference them.
  5. **VisualSpec Label Inspection:** SVG labels are scanned to ensure target answers are masked as `?`.

### 2. 🧮 Deterministic CAS Math Engine & 6 Core Skills
To eliminate LLM arithmetic hallucinations, all calculations are performed by an in-process SymPy engine across 6 core elementary skills:
1. `add_within_20`: Single-digit addition with Ten-Frame visual models.
2. `sub_within_20`: Single-digit subtraction with Number Line visual models.
3. `add_2digit_regroup`: Two-digit addition with Cookie Bakery & Base-Ten Block models.
4. `sub_2digit_borrow`: Two-digit subtraction with Crayon Box Sharing models.
5. `mult_tables`: Times tables (2–10) with Array Grid & Skip-Counting models.
6. `fraction_equivalent`: Fraction comparison with interactive Fraction Bar models.

### 3. 🎨 Deterministic SVG Visual Scaffolding
Visual models are generated via pure deterministic Python builders (`orchestrator/app/services/visuals/`), **never by the LLM**. The frontend renders them with pure SVG components:
- `<TenFrameSVG />`: 10-slot counter frames for foundational counting.
- `<NumberLineSVG />`: Dynamic jumps and hops along a number line.
- `<BaseTenBlocksSVG />`: Hundreds flats, tens rods, and unit cubes.
- `<ArrayGridSVG />`: Rows and columns for multiplication concepts.
- `<FractionBarSVG />`: Partitioned strips for equivalent fractions.
- `<BarModelSVG />`: Singapore-style part-whole tape diagrams.

### 4. 🔍 Word Problem Parse Verification Pipeline
Before solving word problems, inputs pass through a 7-stage deterministic verification pipeline:
1. **JSON Extraction:** Operands, operation, and unit extracted from input.
2. **Operand Existence:** Operands must exist verbatim in student text.
3. **Number Coverage:** No unparsed numbers left unaccounted for.
4. **Cue Word Sanity:** Key phrases (e.g., *"more"*, *"in all"*, *"left over"*) match the chosen operation.
5. **Confidence Gate:** If parse confidence is `< 0.75`, the system generates a **Free Child Confirmation Prompt**:
   > *"Are we solving: 🍎 15 + 27 apples? [Yes] [No]"*  
   *(Zero quota charged until the child confirms).*

### 5. ⏳ Two-Phase Problem Quota (Asia/Phnom_Penh UTC+7)
- Students receive **10 new problems per day** (resets at midnight 00:00 Asia/Phnom_Penh).
- **100% Free Pedagogical Actions:** Hints, visual model generation, answer checks, step navigation, and parse confirmations never deduct from student quotas.
- Uses a two-phase check/commit pattern against the PostgreSQL `usage_ledger`.

### 6. 📊 Unified Gap Report (`gap_events`)
All system, learner, and curriculum gaps are triaged into PostgreSQL `gap_events`:
- **Content Gaps:** Math topics or grade levels not yet supported by the skill templates.
- **Learner Misconceptions:** Repeated mistakes on specific milestones (e.g. adding columns left-to-right).
- **System Anomalies:** Leak Guard interventions, LLM timeouts, and parse failures.
- **Weekly Digest:** Generates actionable teacher and admin markdown reports via `scripts/generate_admin_digest.py`.

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── docker-compose.yml          # 4-container stack (Postgres, Ollama, Orchestrator, Frontend)
│   ├── docker-compose.full.yml     # Distributed profile (Redis, Qdrant, MinIO)
│   ├── orchestrator/               # Core FastAPI gateway & Socratic engine
│   │   ├── app/
│   │   │   ├── api/                # REST endpoints (/api/v1/query, /health, /auth, /upload)
│   │   │   ├── core/               # Configuration & environment settings
│   │   │   ├── infrastructure/     # PostgreSQL 16 database connector
│   │   │   └── services/           # Socratic graph, intent NLU, CAS engine, guardrails
│   │   │       ├── auth/           # Class Code + 4-digit PIN authentication
│   │   │       ├── guardrails/     # Leak Guard v2, PII scrubber, escalation dispatcher
│   │   │       ├── nlu/            # Fast intent router & normalizer
│   │   │       ├── quota/          # Two-phase quota guard & usage ledger
│   │   │       ├── socratic/       # LangGraph state machine & 6 math skills
│   │   │       ├── telemetry/      # Unified gap recorder & pipeline tracer
│   │   │       └── visuals/        # Deterministic SVG VisualSpec builders
│   │   └── requirements.txt
│   ├── ingestion/                  # Curriculum chunker, embedder, and vector pipeline
│   └── testing/                    # Comprehensive test suites & release gate
│       ├── data/                   # 50 Math worksheets & 100 Adversarial leak cases
│       ├── evaluation/             # Adversarial & golden verification evaluators
│       ├── integration/            # Container health & upload tests
│       ├── tools/                  # Automated release-gate runner (`run_release_gate.py`)
│       └── unit/                   # Modular unit tests (auth, CAS, leak guard, quota)
├── docs/                           # Authoritative system documentation & designs
│   ├── CURRENT_STATUS_AND_PENDING_FEATURES.md  # Live progress & pending features
│   ├── ReanMore_Architecture_v2.1.md          # Master architecture specification
│   ├── digests/                    # Evaluation & audit digests
│   ├── pilot/                      # Classroom pilot observation protocol & consent
│   └── plans/                      # Phase 0-5 phased roadmap & status matrix
├── frontend/                       # Interactive React 19 web application
│   ├── src/
│   │   ├── api/                    # Orchestrator client & schemas
│   │   ├── components/             # StepChatBubble, StepCard, MathKeypad, Header
│   │   │   └── visual/             # Pure SVG models (TenFrame, NumberLine, BaseTen, etc.)
│   │   ├── services/               # Answer validation & session state services
│   │   ├── types/                  # StepItem, VisualSpec, and Chat interfaces
│   │   └── utils/                  # Kid analogy generator, language helpers, normalizers
│   └── package.json
└── scripts/                        # Maintenance & deployment automation utilities
    ├── generate_admin_digest.py    # Generates weekly admin & teacher gap digests
    └── README.md
```

---

## 🛠️ Quick Start Guide

### Prerequisites
- **Node.js**: v18+ and **npm**
- **Python**: v3.11+
- **Docker & Docker Compose**: v2.20+
- **Ollama** *(recommended on host)*: `ollama run qwen3.5:4b`

---

### 1. Backend Setup (Streamlined 4-Container Stack)

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Copy the sample environment file:
   ```bash
   cp .env.example .env
   ```
3. Start the 4-container stack (PostgreSQL, Orchestrator, Frontend; add `--profile container-ollama` to containerize the model):
   ```bash
   docker compose up -d
   ```
   The frontend is served at [http://localhost:3000](http://localhost:3000).
   > *Note:* If you do not have Ollama installed on your host OS, launch the containerized profile:  
   > `docker compose --profile container-ollama up -d`

4. Verify backend health:
   ```bash
   curl http://localhost:9000/health
   # Expected response: {"status":"healthy","database":"connected","version":"2.1.0"}
   ```

---

### 2. Frontend Setup (React 19 + Vite)

1. Open a new terminal and navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install frontend dependencies:
   ```bash
   npm install
   ```
3. Start the Vite development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing & Verification

Backend (from `backend/`):

```powershell
& .venv\Scripts\python.exe -m pytest -q                 # 651 passed
& .venv\Scripts\python.exe testing\evaluation\golden_verifier.py        # 50/50 worksheets
& .venv\Scripts\python.exe testing\evaluation\adversarial_evaluator.py  # 100/100 probes, 0 leaks
& .venv\Scripts\python.exe testing\tools\run_release_gate.py            # pre-release gate
```

Frontend (from `frontend/`):

```powershell
npm test        # vitest: real test runner (not a build)
npm run build   # production bundle
```

> Tests are pinned to the in-process mock LLM provider (`backend/testing/conftest.py`),
> so the suite is deterministic and does not require Ollama, Gemini, or a database.

---

## 🗺️ Phased Implementation Roadmap

| Phase | Milestone | Scope | Status |
| :---: | :--- | :--- | :---: |
| **0** | **Runtime Profiling & Benchmarks** | Concurrency control (`INFLIGHT=1`), single-model latency profiling. | **COMPLETED** |
| **1** | **Streamlined Infra & Core Socratic Engine** | 4-container stack, Leak Guard v2, in-process CAS, 6 Skill Templates, SVG models, Quota Guard, Gap Recorder, Kid Pedagogy. | **COMPLETED** |
| **2** | **Golden Evaluation & Real-Kid Pilot** | 50 Math worksheets & 100 Adversarial leak cases, real-classroom pilot study. | **READY FOR PILOT** |
| **3** | **Curriculum Science RAG** | Offline Qdrant vector retrieval for MoEYS Grade 1–6 Science textbooks. | **IN PROGRESS** |
| **4** | **Offline Worksheet Photo Ingress** | Camera / photo upload OCR parsing into multi-exercise stepper. | **PENDING** |
| **5** | **Bilingual Khmer (ភាសាខ្មែរ) NLP** | Unspaced script tokenization (`khmer-nltk`) and bilingual Socratic UI. | **PENDING** |

For detailed gap tracking and upcoming deliverables, refer to **[`docs/CURRENT_STATUS_AND_PENDING_FEATURES.md`](docs/CURRENT_STATUS_AND_PENDING_FEATURES.md)**.

---

## 📄 License & Attribution
Developed for the **Khmer Enterprise (KE) STEM Educational Initiative**.  
All rights reserved. Powered by open-weights models and privacy-preserving offline architectures.
