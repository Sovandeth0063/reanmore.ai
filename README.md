# ReanMore.ai (រៀនបន្ថែម) 🚀

> **Intelligent Elementary STEM Socratic Tutoring Ecosystem (Grades 1–6)**  
> Built for accessible, privacy-preserving, and pedagogically grounded learning in Math & Science, supporting step-by-step problem decomposition without ever giving away direct answers.

---

## 🌟 Overview

**ReanMore.ai** is a specialized educational AI platform tailored for elementary school students (ages 6–12). Unlike generic chatbots that instantly reveal final answers, ReanMore acts as a warm, encouraging Socratic tutor. It guides children through multi-step milestones using concrete, kid-friendly analogies (such as *"Cookie Bakery Boxes"*, *"Tall Ten-Towers"*, and *"Apple Baskets"*), interactive visual diagrams, and adaptive comprehension checks.

---

## 🏗️ Architecture Overview

```text
                               ┌─────────────────────────────────────────┐
                               │       ReanMore Web Frontend             │
                               │  - React 19 + TypeScript + Vite         │
                               │  - Interactive Stepper & StepTrail UI   │
                               │  - On-Card 💡 Helpful Tip Banners       │
                               │  - Tunsay Rabbit Mascot Feedback        │
                               └────────────────────┬────────────────────┘
                                                    │
                                     REST / JSON    │ /api/v1/query
                                                    ▼
                               ┌─────────────────────────────────────────┐
                               │      FastAPI Orchestrator Gateway       │
                               │  - Language & Intent Router             │
                               │  - Multi-Exercise Worksheet Stepper     │
                               │  - Deterministic CAS Math Engine        │
                               │  - Socratic State Machine               │
                               │  - Leak Guard v2 (Zero Direct Answers)  │
                               │  - Student Session & Telemetry State    │
                               └──────┬─────────────────┬────────────────┘
                                      │                 │
                ┌─────────────────────┴───────┐         └─────────────────────────┐
                ▼                             ▼                                   ▼
┌───────────────────────────────┐ ┌───────────────────────────────┐ ┌───────────────────────────────┐
│       PostgreSQL 16           │ │         Redis Stack           │ │       Qdrant Vector DB        │
│ - Student Profiles & Progress │ │ - Real-Time Session Memory    │ │ - MoEYS Curriculum Embeddings │
│ - Daily/Monthly Quota Records │ │ - 10-Problem/Day Rate Limits  │ │ - Grade 1–6 STEM Knowledge    │
└───────────────────────────────┘ └───────────────────────────────┘ └───────────────────────────────┘
```

---

## 🚀 Key Capabilities & Features

### 1. 🎓 Kid-Friendly Socratic Pedagogy
- **No Direct Answer Leakage:** Invariant safety engine mathematically and syntactically prevents the system from dumping final solutions.
- **Relatable Analogies for Young Learners:**
  - **Single Blocks & Finger Counting 🧱🖐️:** Encourages starting with the larger number and counting forward.
  - **Cookie Bakery Boxes 🍪📦:** Regrouping addition conceptualized as packing 10 loose cookies into 1 bakery box.
  - **Tall Ten-Towers 🗼:** Tens and ones place value represented as snapping 10 blocks into a tower.
  - **Unpacking Gift & Crayon Boxes 🎁🖍️:** Borrowing in subtraction taught as opening a 10-pack of crayons to share with friends.
- **Instant On-Card `💡 Helpful Tip`:** High-visibility contextual clue box directly below the problem statement so elementary students never get stuck.

### 2. 🧮 Fast In-Process Math Solver & Verification
- High-speed Computer Algebra System (CAS) solving multi-digit addition, subtraction with borrowing, multiplication, and division.
- Step-by-step milestone decomposition matching elementary school curricula.
- Tolerant student answer normalization (supports spelled numbers, units, comma separations, and conversational answers like *"it is 12 cookies"*).

### 3. 🔬 Curricular Science Exploration
- Interactive Socratic inquiry for Grade 1–6 Science (States of Matter: Solids 🧊, Liquids 💧, Gases 🎈, Plants, Habitats, Energy).
- Multi-step inquiry guiding the student to observe properties before arriving at scientific conclusions.

### 4. 🛡️ Child Safety & Privacy (COPPA / GDPR-K Aligned)
- **Zero Cloud API Dependency Option:** Runs offline on local hardware via quantized open-weights models or containerized microservices.
- **Student Privacy:** Zero personally identifiable information (PII) required; login via simple Class Code + 4-digit PIN.
- **Deflection Guardrails:** Automatically flags and redirects off-topic, unsafe, or non-educational inquiries back to learning.

---

## 📁 Repository Structure

```text
.
├── backend/
│   ├── docker-compose.yml          # Container configuration (Postgres, Redis, Orchestrator)
│   ├── orchestrator/               # Core FastAPI gateway & Socratic engine
│   │   ├── app/
│   │   │   ├── api/                # REST endpoints (/api/v1/query, /health, /auth, etc.)
│   │   │   ├── core/               # App configuration & settings
│   │   │   ├── infrastructure/     # Database & Redis connectors
│   │   │   └── services/           # Socratic graph, intent NLU, CAS engine, guardrails
│   │   └── requirements.txt
│   ├── ingestion/                  # Curriculum PDF/text chunking & Qdrant vector pipeline
│   └── testing/                    # Comprehensive integration & release-gate test suites
├── docs/                           # Architecture specifications, pedagogical designs, pilot logs
│   ├── CURRENT_STATUS_AND_PENDING_FEATURES.md
│   ├── ReanMore_Architecture_v2.1.md
│   ├── pilot/                      # Classroom observation protocol & consent templates
│   └── plans/                      # Detailed implementation status matrix
├── frontend/                       # Interactive web application
│   ├── src/
│   │   ├── api/                    # Backend API client connectors
│   │   ├── components/             # StepChatBubble, StepCard, MathKeypad, HomeworkScanner
│   │   ├── services/               # Answer validation & session services
│   │   └── utils/                  # Kid analogy generator, language helpers, normalizers
│   └── package.json
└── scripts/                        # Maintenance & deployment automation utilities
```

---

## 🛠️ Getting Started

### Prerequisites
- **Node.js**: v18+ and **npm**
- **Python**: v3.11+
- **Docker & Docker Compose**: v2.20+

### 1. Backend Setup
1. Navigate to the backend directory:
   ```bash
   cd backend
   ```
2. Copy the sample environment file:
   ```bash
   cp .env.example .env
   ```
3. Start the core backend infrastructure:
   ```bash
   docker compose up -d
   ```
4. Verify backend health:
   ```bash
   curl http://localhost:9000/health
   # Response: {"status":"healthy","database":"connected","version":"2.1.0"}
   ```

### 2. Frontend Setup
1. In a new terminal, navigate to the frontend directory:
   ```bash
   cd frontend
   ```
2. Install dependencies:
   ```bash
   npm install
   ```
3. Start the development server:
   ```bash
   npm run dev
   ```
4. Open [http://localhost:5173](http://localhost:5173) in your browser.

---

## 🧪 Testing & Quality Gates

Run the automated verification suite to validate math decomposition, science inquiry, and leak-free guardrails:
```bash
python scratch/test_endpoints.py
```

---

## 🗺️ Roadmap & Pending Features

See [`docs/CURRENT_STATUS_AND_PENDING_FEATURES.md`](docs/CURRENT_STATUS_AND_PENDING_FEATURES.md) for full tracking:
- **Offline Photo OCR / VLM Ingress:** Direct camera / image upload parsing of physical paper worksheets into the multi-exercise stepper.
- **Bilingual Khmer (ភាសាខ្មែរ) NLP:** Unspaced script segmentation (`khmer-nltk`) and MoEYS Grade 1–6 textbook bilingual alignment.
- **Live Classroom Pilot Trial:** Physical classroom observational study with elementary school students.

---

## 📄 License
This project is developed for the Khmer Enterprise STEM educational initiative. All rights reserved.
