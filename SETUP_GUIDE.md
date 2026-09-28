# 🚀 Fullstack Setup & Deployment Guide

Welcome to the **WEG Homework AI & Socratic Tutoring Ecosystem**! This guide details how to install, configure, and run both the **Backend microservices** and the **Frontend Web Application**.

---

## 🏗️ Architecture & Port Mapping

| Service | Port | Description | Tech Stack |
| :--- | :--- | :--- | :--- |
| **Frontend Web App** | `5173` | Interactive Socratic UI, Tunsay mascot, Worksheet bar | React 19, Vite, Tailwind CSS |
| **Orchestrator Gateway** | `9000` | Socratic LangGraph state machine, query router, validator | FastAPI, LangGraph, Redis |
| **Math Service** | `9001` | Symbolic Math solver & step-by-step verification | FastAPI, SymPy, Gemini |
| **Science Service** | `9002` | Science problem solver (Physics, Chemistry, Biology) | FastAPI, Gemini, SymPy |
| **Homework Scanner** | `9003` | Multimodal VLM OCR, worksheet layout parser | FastAPI, PaddleOCR, Gemini VLM |
| **Redis** | `6379` | State persistence & checkpointing | Redis Stack |
| **PostgreSQL** | `5432` | Student profiles & analytics | PostgreSQL 15 |
| **Qdrant** | `6333` | Vector database for RAG & curriculum indexing | Qdrant |

---

## 📋 Prerequisites

Before starting, ensure your system has:
1. **Python**: Version `3.10` or higher (`3.11` recommended)
2. **Node.js**: Version `18.x` or `20.x` with `npm`
3. **Git**: Installed and available in PATH
4. **API Key**: A valid [Google Gemini API Key](https://aistudio.google.com/)
5. *(Optional)* **Docker & Docker Desktop**: For running the entire containerized stack

---

## 🔑 1. Environment Configuration

### Root Environment File (`.env`)
Copy `.env.example` in the root directory to `.env`:

```bash
# Windows PowerShell
Copy-Item .env.example .env

# Bash / Linux / macOS
cp .env.example .env
```

Open `.env` and fill in your Gemini API key:
```env
# Required for Gemini AI calls
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-flash-lite-latest

# Service Ports (Default 9000-series)
ORCHESTRATOR_PORT=9000
MATH_SERVICE_PORT=9001
SCIENCE_SERVICE_PORT=9002
HOMEWORK_SCANNER_PORT=9003

# Downstream URLs (Local development defaults)
MATH_SERVICE_URL=http://localhost:9001
SCIENCE_SERVICE_URL=http://localhost:9002
HOMEWORK_SCANNER_URL=http://localhost:9003

# Databases (Local fallback or Docker)
REDIS_URL=redis://localhost:6379/0
QDRANT_HOST=localhost
QDRANT_PORT=6333
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=science_chatbot
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/science_chatbot
```

### Frontend Environment File (`frontend/.env`)
Copy `frontend/.env.example` to `frontend/.env`:
```bash
# Windows PowerShell
Copy-Item frontend\.env.example frontend\.env

# Bash / Linux / macOS
cp frontend/.env.example frontend/.env
```

---

## ⚡ Option A: Quick Start (Windows PowerShell - Recommended)

If you are on Windows, we provide preconfigured scripts for one-click startup and shutdown:

### 1. Install Dependencies
```powershell
# Create Python virtual environment if not already created
python -m venv .venv
.\.venv\Scripts\pip install -r requirements.txt

# Install Frontend dependencies
cd frontend
npm install
cd ..
```

### 2. Launch All Services (Backend + Frontend)
```powershell
.\start_all.ps1
```
This automatically launches all 4 backend microservices and the Vite frontend dev server in separate terminal windows.

### 3. Stop All Services
```powershell
.\stop_all.ps1
```
This terminates all processes listening on ports `9000`, `9001`, `9002`, `9003`, and `5173`.

---

## 🐳 Option B: Backend & Databases via Docker

If you prefer running the backend microservices and databases (Redis, PostgreSQL, Qdrant) in Docker containers while running the frontend locally:

### 1. Launch Backend & Databases in Docker:
```bash
# Build and start all backend microservices + DBs
docker compose up --build

# Run in background (detached mode)
docker compose up -d --build

# Stop the docker stack
docker compose down
```

### 2. Run Frontend Web UI (in another terminal):
```bash
cd frontend
npm install
npm run dev
```

The frontend will run at `http://localhost:5173` and automatically proxy requests to the backend microservices.

---

## 🛠️ Option C: Manual Setup (Step-by-Step for Any OS)

Follow these steps if you want to start each service manually or are developing on Linux / macOS:

### 1. Setup Backend Virtual Environment & Dependencies
```bash
# 1. Create and activate virtualenv
python -m venv .venv

# On Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# On Linux/macOS:
source .venv/bin/activate

# 2. Install backend dependencies
pip install -r requirements.txt
```

### 2. Setup Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### 3. Start Backend Microservices (Separate Terminals)

**Terminal 1 — Homework Scanner (Port 9003)**:
```bash
cd backend/homework_ocr_vlm
python run.py
```

**Terminal 2 — Math Service (Port 9001)**:
```bash
cd backend/services/math_service
uvicorn app.main:app --port 9001 --reload
```

**Terminal 3 — Science Service (Port 9002)**:
```bash
cd backend/services/science_service
uvicorn app.main:app --port 9002 --reload
```

**Terminal 4 — Orchestrator Gateway (Port 9000)**:
```bash
cd backend/orchestrator
uvicorn app.main:app --port 9000 --reload
```

### 4. Start Frontend Web Server (Terminal 5)
```bash
cd frontend
npm run dev
```

---

## 🌐 Access Points & Verification

Once running, verify everything is healthy using the following endpoints:

| Application / API | URL | Verification |
| :--- | :--- | :--- |
| **Frontend Web App** | [http://localhost:5173](http://localhost:5173) | Socratic Chat, Mascot & Worksheets |
| **Orchestrator Swagger** | [http://localhost:9000/docs](http://localhost:9000/docs) | Interactive API playground |
| **Math Service Swagger** | [http://localhost:9001/docs](http://localhost:9001/docs) | Math solver API |
| **Science Service Swagger** | [http://localhost:9002/docs](http://localhost:9002/docs) | Science solver API |
| **Homework Scanner Docs** | [http://localhost:9003/docs](http://localhost:9003/docs) | OCR & VLM parsing API |

---

## 🧪 Running Tests

### Backend Unit Tests
```bash
python -m pytest backend/testing/unit
```

### Homework Scanner Tests
```bash
python -m pytest backend/homework_ocr_vlm/tests/test_pipeline.py -m "not integration"
```

### Frontend Typecheck & Build Test
```bash
cd frontend
npm run build
```

---

## ❓ Troubleshooting

### 1. `Port already in use` error
- Run `.\stop_all.ps1` on Windows, or check which process is occupying the port:
  ```powershell
  Get-NetTCPConnection -LocalPort 9000,9001,9002,9003,5173
  ```
  On Linux/Mac:
  ```bash
  lsof -i :9000,9001,9002,9003,5173
  ```

### 2. Missing `GEMINI_API_KEY`
- If you see `Google API key not found` errors, verify that `.env` exists in the project root and contains `GEMINI_API_KEY=AIza...`.

### 3. Frontend proxy connection refused
- The Vite dev server proxies `/api` calls to `http://localhost:9000` and OCR calls to `http://localhost:9003`. Ensure the Orchestrator (9000) and Homework Scanner (9003) are running.
