# 🛠️ Frontend Services Architecture

This folder contains the API services and dynamic AI connectors for the ReanMore application.

---

## 📁 Services Directory Map

```
frontend/src/services/
├── answerValidationService.ts # ✅ Local fast-path answer checks for step UI
├── authService.ts             # 🔐 Session / profile persistence
├── geminiService.ts           # 🤖 Dynamic Google Gemini / backend AI tutor integration
├── llmControllerService.ts    # 🧭 Model routing / request control
└── ocrService.ts               # 📸 VLM vision & homework OCR scanning (Phase 4, flag-gated)

Dynamic bilingual translation lives in `src/api/translateApi.ts` (backend `/api/translate`).
```

---

## ⚡ Content Source

All Socratic content is generated dynamically by the backend prompts. There is no
offline hardcoded case matcher or pre-built tutor response provider.
