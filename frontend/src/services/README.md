# 🛠️ Frontend Services Architecture

This folder contains all API services, dynamic AI connectors, and offline fallback providers for the ReanMore application.

---

## 📁 Services Directory Map

```
frontend/src/services/
├── geminiService.ts          # 🤖 Dynamic Google Gemini / Backend AI Tutor Integration
├── ocrService.ts             # 📸 VLM Vision & Homework OCR Scanning Service
├── translationService.ts     # 🌐 Bilingual Khmer-English Translation & Curriculum Terminology
├── caseMatcher.ts            # 🔍 Offline Keyword & Problem Matcher (Hardcoded Fallback)
└── hardcodedTutorProvider.ts # 💾 Offline Socratic Response Generator (Hardcoded Fallback)
```

---

## ⚡ Dynamic vs. Hardcoded Separation

- **Dynamic Services**:
  - `geminiService.ts` and `ocrService.ts` handle live AI vision, adaptive grade prompting, and dynamic Socratic questioning.
- **Offline / Hardcoded Fallbacks**:
  - `caseMatcher.ts` and `hardcodedTutorProvider.ts` pair scanned samples with pre-built mock exercises in `src/data/` if the student is offline or testing mock cases.
