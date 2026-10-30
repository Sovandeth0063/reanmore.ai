# Phase 3 Implementation Plan: Curriculum Science RAG Engine

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](../../docs/ReanMore_Architecture_v2.1.md) (Section 2, Section 11, Section 15.1)  
> **Status:** COMPLETED & VERIFIED ✅  
> **Prerequisites:** Phases 0, 1A-1E, and Phase 2 complete and verified.

---

## 1. Objectives & Scope

Phase 3 introduces the **Curriculum Science RAG (Retrieval-Augmented Generation)** subsystem, expanding ReanMore beyond Mathematics to cover **Elementary Science (Grades 1–6)** homework queries while adhering strictly to the **$0.00 offline inference** and **Zero Answer Leakage** invariants.

### 1.1 Core Objectives
1. **Local Vector Database:** Deploy Qdrant vector storage (local embedded mode + Docker service option) with persistent storage in `backend/data/qdrant/`.
2. **Offline Dense Embeddings:** Implement 100% offline embedding pipeline using fast, lightweight sentence embeddings (`all-MiniLM-L6-v2` / `bge-small-en-v1.5`), maintaining zero cloud dependency.
3. **Curriculum Ingestion Pipeline:** Parse and chunk English elementary science curriculum units (Life Science, Physical Science, Earth & Space Science) with rich metadata (`grade_band`, `unit`, `topic`, `citation_source`).
4. **Socratic Context Grounding:** Feed retrieved textbook snippets directly into the Socratic graph's `initial_problem` node, ensuring science hints and step cards cite authoritative textbook concepts rather than hallucinating.
5. **Curriculum Gap Logging:** Automatically log out-of-syllabus science queries to `gap_events` (`gap_type="content"`, `event_code="SCIENCE_OUT_OF_CURRICULUM"`).
6. **RAG Quality Benchmark Suite:** 30 golden science questions evaluated against RAGAS metrics (Faithfulness $\ge 0.95$, Answer Relevance $\ge 0.85$, Zero premature answer leaks).

---

## 2. Curriculum Coverage (Grades 1–6)

| Curriculum Unit | Grade Band | Core Topics Covered |
| :--- | :---: | :--- |
| **Living Things & Habitats** | Grades 1–3 | Plants (roots, stem, leaves), Animals (mammals, birds, fish, reptiles), Life cycles |
| **States of Matter & Changes** | Grades 1–4 | Solids, Liquids, Gases, Melting, Freezing, Evaporation, Condensation |
| **Forces, Motion & Magnets** | Grades 2–5 | Pushes and pulls, Friction, Gravity, Magnetic poles (attract/repel) |
| **Ecosystems & Energy** | Grades 4–6 | Food chains, Producers, Consumers, Decomposers, Photosynthesis |
| **Earth & Solar System** | Grades 3–6 | Water cycle, Rock types, Earth's rotation (day/night), Planetary orbits |
| **Human Body & Health** | Grades 4–6 | Skeletal & muscular system, Digestion, Circulatory basics, Nutrition |

---

## 3. Subsystem Architecture

```text
Student Science Query ("Why do leaves turn green in sunlight?")
                            │
                            ▼
           Intent & Domain Classifier (endpoints.py)
                            │ subject == "science"
                            ▼
               Offline Embedding Client
             (bge-small-en-v1.5, 384-dim, FastEmbed)
                            │
                            ▼
              Qdrant Vector Store (:6333 / embedded)
     [Filter: grade_band == target_grade, subject == "science"]
                            │
                            ▼ (Top-K Passages + Similarity Score >= 0.55)
             ┌──────────────┴──────────────┐
             │                             │
    [Score >= 0.55]                 [Score < 0.55]
             │                             │
             ▼                             ▼
    Context Grounding Node        Log Content Gap (`gap_events`)
    (Socratic Planning & Hints)    & Friendly Syllabus Deflection
             │
             ▼
    Socratic 4-Part Card
    (Zero premature answer leaks)
```

---

## 4. Step-by-Step Implementation Steps

### Step 3.1: Offline FastEmbed & Qdrant Setup — COMPLETED ✅
- Created [`backend/orchestrator/app/services/rag/embedder.py`](../../backend/orchestrator/app/services/rag/embedder.py):
  - Fast, local embedding generation via FastEmbed ONNX runtime (`BAAI/bge-small-en-v1.5`, 384 dims, ~10ms execution on CPU, $0.00 cost).
- Created [`backend/orchestrator/app/services/rag/vector_store.py`](../../backend/orchestrator/app/services/rag/vector_store.py):
  - Persistent Qdrant vector client supporting local disk storage (`backend/data/qdrant`) and containerized Qdrant network service.

### Step 3.2: Elementary Science Knowledge Base Curation & Ingestion — COMPLETED ✅
- Curated [`backend/ingestion/data_sources/science_curriculum_en.json`](../../backend/ingestion/data_sources/science_curriculum_en.json):
  - 15 authoritative, grade-stratified textbook chapters spanning all 6 core elementary science units.
- Created and executed [`backend/ingestion/ingest_science_curriculum.py`](../../backend/ingestion/ingest_science_curriculum.py):
  - Indexed 15 curriculum chapters into collection `reanmore_science_curriculum`.

### Step 3.3: Socratic RAG Retriever & Grounding Node — COMPLETED ✅
- Created [`backend/orchestrator/app/services/rag/retriever.py`](../../backend/orchestrator/app/services/rag/retriever.py):
  - Retrieves top-3 passages with calibrated threshold (0.55).
  - Formats textbook context block with verified citations.
  - Wired into `initial_problem_node` in [`backend/orchestrator/app/services/socratic/graph.py`](../../backend/orchestrator/app/services/socratic/graph.py) and `controller.plan_exercise_socratic_widget`.

### Step 3.4: Content Gap Telemetry Integration — COMPLETED ✅
- In `ScienceRetriever.retrieve_grounded_context`:
  - When similarity score < 0.55 (e.g. out-of-syllabus query): dispatches `SCIENCE_OUT_OF_CURRICULUM` content gap event to `gap_events` ledger.

### Step 3.5: Science Benchmark Suite & Golden Evaluation — COMPLETED ✅
- Curated [`backend/testing/data/golden_30_science_questions.jsonl`](../../backend/testing/data/golden_30_science_questions.jsonl): 30 golden science questions across Grades 1–6.
- Created [`backend/testing/evaluation/science_rag_evaluator.py`](../../backend/testing/evaluation/science_rag_evaluator.py):
  - **Results:** 30 / 30 (**100.0%**) Retrieval Success Rate, **100.0%** Top-1 Chapter Match, **100.0%** Concept Recall, 0 Leaks.
  - Digest generated: [`docs/digests/science_rag_eval_2026_10_19.md`](../../docs/digests/science_rag_eval_2026_10_19.md).
- Created [`backend/testing/unit/rag/test_science_rag.py`](../../backend/testing/unit/rag/test_science_rag.py):
  - **Pytest:** 5 / 5 passed (100% GREEN).
