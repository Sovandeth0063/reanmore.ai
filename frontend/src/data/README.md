# 📚 Frontend Hardcoded Datasets & Mock Curriculum

This directory contains all offline, mock, and curriculum datasets used by the ReanMore frontend for demonstrations, offline fallback matching, and mock scanner worksheets.

---

## 📁 Files & Purpose

| File | Purpose | Description |
| :--- | :--- | :--- |
| **`math.json`** | 🧮 Math Problem Catalog | Pre-indexed Grade 1–6 elementary math problems, containing multi-part step widgets (number lines, object counters, place value grids). |
| **`science.json`** | 🔬 Science Problem Catalog | Pre-indexed elementary science problems (magnets, plant growth, water cycle, animal classification, states of matter). |
| **`mockProblems.ts`** | 📑 Interactive Mock Worksheets | Ready-to-use worksheet problems with full Khmer/English bilingual text, step questions, and visual widget payloads for offline scanner testing. |
| **`hardcodedCases.ts`** | 🎯 Keyword & Case Matchers | Offline matcher rules that pair scanned image text and student questions to pre-designed interactive pedagogical steps. |
| **`tutorQuestions.ts`** | 💡 Starter Prompt Chips | Quick-suggestion chips and starter prompts displayed in the chat interface to help students begin asking STEM questions. |

---

## 🔄 Dynamic vs. Hardcoded Flow

1. **Online (Gemini / AI Backend)**:
   - Queries and scanned homework are sent to the AI API, dynamically decomposing questions into 4-part Socratic steps and generating responsive feedback.
2. **Offline Fallback**:
   - If the network or LLM is offline, `caseMatcher.ts` and `hardcodedTutorProvider.ts` load corresponding step cards directly from `mockProblems.ts`, `math.json`, and `science.json`.
