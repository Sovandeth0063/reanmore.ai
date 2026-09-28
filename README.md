# WEG Homework AI & Socratic Tutoring Ecosystem 🎓

> **Integrated multimodal homework digitization and AI Socratic tutoring system** for elementary school students (Grades 1–6) in **Math** and **Science** (Physics, Chemistry, Biology), supporting both **English** and **Khmer**.

---

## 🏗️ Architecture Overview

```text
                      ┌─────────────────────────────────────────┐
                      │    Homework Scanner & OCR (Port 9003)   │
                      │   Universal VLM + Precision Geometry    │
                      └────────────────────┬────────────────────┘
                                           │ Scanned JSON
                                           ▼
┌─────────────────────────────────────┐                  ┌─────────────────────────────────────────┐
│        Frontend Web UI (Port 5173)  │ ──── /api/query ─▶│      Backend Orchestrator (Port 9000)   │
│ - React 19 + Vite + Tailwind CSS    │                  │ - LangGraph Socratic State Machine      │
│ - Tunsay Mascot & Stepper Card      │◀─── Socratic ────│ - Math Microservice (Port 9001)         │
│ - Multi-Exercise Worksheet Bar      │     Responses    │ - Science Microservice (Port 9002)      │
└─────────────────────────────────────┘                  │ - Redis + Postgres + Qdrant Databases   │
                                                         └─────────────────────────────────────────┘
```

---

## 📂 Project Structure

```text
Science_chatbot/
├── docker-compose.yml              # Multi-Service Docker Orchestration
├── start_all.ps1                   # One-click Windows PowerShell startup script
├── .env.example                    # Example environment configuration
├── pytest.ini                      # Central pytest configuration
│
└── backend/                        # 🧠 Complete Backend System & Microservices
    ├── orchestrator/               # Main Gateway API & LangGraph State Machine (Port 9000)
    ├── homework_ocr_vlm/           # Universal VLM Homework Extraction Service (Port 9003)
    │   ├── app/                    # Layout, OCR, Preprocessing, VLM
    │   ├── sample_inputs/          # Test images (test1.png)
    │   ├── sample_outputs/         # Benchmark JSON extractions
    │   ├── scripts/                # test_image_scanner.py, run_worksheet_test.py
    │   └── tests/                  # Pytest pipeline tests & fixtures
    ├── services/
    │   ├── math_service/           # Math solver (SymPy + LLM validator, Port 9001)
    │   └── science_service/        # Science solver (Physics, Chemistry, Biology, Port 9002)
    ├── testing/                    # Test Suites & Developer Playgrounds
    │   ├── unit/                   # Gateway, Guardrails, NLU, Socratic, Solvers
    │   ├── integration/            # End-to-end multi-service tests
    │   └── tools/                  # interactive_chat.py, interactive_nlu_tester.py
    └── ingestion/                  # Qdrant Vector Data Ingestion Pipeline
```

---

## 🚀 Quick Start Guide

> 📖 **For complete step-by-step setup instructions, environment config, and troubleshooting, see the [Fullstack Setup Guide](SETUP_GUIDE.md).**

### Option 1: Docker Stack (Backend & Databases)
```bash
docker compose up --build
```
Then in a separate terminal:
```bash
cd frontend && npm install && npm run dev
```
This launches:
- **Orchestrator Gateway**: `http://localhost:9000`
- **Homework Scanner**: `http://localhost:9003`
- **Math Service**: `http://localhost:9001`
- **Science Service**: `http://localhost:9002`
- **Databases**: Redis (`6379`), PostgreSQL (`5432`), Qdrant (`6333`)

### Option 2: Local Development
1. **Launch all 4 backend microservices**:
   ```powershell
   .\start_all.ps1
   ```
2. Open `http://localhost:5173` in your browser.

---

## 🧪 Testing

Run all unit tests:
```powershell
.\.venv\Scripts\python.exe -m pytest testing/unit
```

Run Homework Scanner tests:
```powershell
.\.venv\Scripts\python.exe -m pytest services/homework_scanner/tests/test_pipeline.py -m "not integration"
```

Interactive Socratic CLI Tutor:
```powershell
.\.venv\Scripts\python.exe testing/tools/interactive_chat.py
```
