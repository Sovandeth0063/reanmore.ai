# MVP Close-Out Report â€” ReanMore v2.1

**Date:** 2026-10-30  
**Branch:** `chesda` (working tree; no commits created)  
**Scope:** P0/P1/P2 backlog from the close-out plan.

---

## 1. Baseline vs After

| Item | Claimed / baseline (observed) | After |
| :--- | :--- | :--- |
| Backend suite | 1 collection error (`testing/unit/solvers/test_solvers.py`, legacy `app.validator`) + 4 failed / 647 passed when ignored | **651 passed, 0 failed, 0 errors** |
| Golden worksheets | â€œ50/50â€ unverified in this checkout | **50 / 50**, CAS parity 100%, 0 leaks |
| Adversarial probes | â€œ100/100, 0 leaksâ€ unverified | **100 / 100**, quarantine 100%, 0 leaks |
| Release gate | â€” | **GO** (5/5 gates) |
| Frontend `npm test` | `vite build` (build reported as a test pass) | **vitest**: 3 files / 19 tests passed |
| Frontend typecheck | â€” | `tsc --noEmit`: 0 errors |
| Frontend build | â€” | `vite build`: success |
| Compose topology | test expected 9 services; compose had 3 | **4 services** (Postgres, Ollama, Orchestrator, Frontend) |
| OCR | built, disabled, cloud-dependent | **deferred + gated**: `ENABLE_API_OCR=false`, `/api/upload/*` â†’ 404 |
| Khmer | stub toggle; `/api/translate` â†’ 501 | **toggle shipped**; translate enabled; full NLP deferred |
| Legacy microservices | in-tree and imported by tests | archived to `legacy/`; no active imports |

Observed baseline note: the previously reported â€œ622 collectedâ€ was not reproducible in this
checkout; the real baseline was one collection error plus 651 collected tests (647 pass, 4 fail).

---

## 2. Evidence (commands actually run)

```powershell
# backend/
& .venv\Scripts\python.exe -m pytest -q -p no:warnings
# 651 passed in 80.21s

& .venv\Scripts\python.exe testing\evaluation\golden_verifier.py
# Total 50 | Passed 50/50 (100%) | CAS 100% | Leaks 0%
# docs/digests/golden_eval_2026_10_30.md

& .venv\Scripts\python.exe testing\evaluation\adversarial_evaluator.py
# Total 100 | Passed 100/100 (100%) | Quarantine 100%
# docs/digests/adversarial_eval_2026_10_30.md

& .venv\Scripts\python.exe testing\tools\run_release_gate.py
# GO â€” 5/5 gates pass
# docs/RELEASE_QUALIFICATION_REPORT.md

# frontend/
npm test        # 3 files, 19 tests passed (vitest)
.\node_modules\.bin\tsc.cmd --noEmit   # 0 errors
npm run build   # built successfully
```

---

## 3. What changed

### T1 â€” Backend suite green
- Added deterministic, offline test isolation in `backend/testing/conftest.py`:
  pins `LLM_PRIMARY_PROVIDER=mock` (no Ollama/Gemini/DB dependency).
- Added a `stub_socratic_llm` fixture returning a valid 2-step widget for graph tests
  that have no deterministic skill match.
- Archived the legacy microservices and their two tests (see T6), removing the
  collection error at its root instead of skipping it.

### T2 â€” OCR decision: DEFERRED
- Added `ENABLE_API_OCR` (default `false`) in `backend/orchestrator/app/core/config.py`.
- `/api/upload/ocr` and `/api/upload/select` return `404` while disabled
  (`backend/orchestrator/app/api/upload.py`), with a test for the default.
- Aligned `.env.example`, `README.md`, `docs/CURRENT_STATUS_AND_PENDING_FEATURES.md`,
  and `docs/plans/README.md` to â€œdeferred, out of MVPâ€.

### T3 â€” Refactor landed
- Deleted the dead 214 KB `frontend/src/services/translationService.ts` and its stale
  `vite.config.ts` manual-chunk entry; updated `src/services/README.md`.
- Typecheck and production build pass.

### T4 â€” Real frontend test runner
- `frontend/package.json`: `test` â†’ `vitest run`, added `test:watch`.
- Converted the two existing `node:test` files to vitest (they previously never ran)
  and added `src/utils/language.test.ts`.
- CI: added a `frontend` job that runs `npm ci`, `npm test`, `npm run build`.

### T5 â€” Khmer toggle shipped; full NLP deferred
- Header + Profile language toggle (EN â†” ážáŸ’áž˜áŸ‚ážš), persisted in the profile.
- Removed the eight hardcoded `isKhmer = false` stubs; components now derive locale
  from `language` / `profile.language`.
- Fixed `t()` and `cleanBilingualOption()` to honour `km`.
- Added `localizeStepsForKhmer()` (`frontend/src/components/chat/chatUtils.tsx`):
  dynamic step text is translated through `POST /api/translate`, with English fallback.
- `ENABLE_KHMER_LANGUAGE` now defaults to `true`; full segmentation/parser/MoEYS
  ingestion are documented as v2.2 and out of MVP.

### T6 â€” Legacy pruning
- Moved `backend/services/{math_service,science_service}` and
  `testing/unit/solvers/test_solvers.py`, `testing/unit/test_math_solver.py`
  to `legacy/microservices/` (with `legacy/README.md`).
- Moved stale root copies (`orchestrator/`, `testing/`, `services/`, `ingestion/`) and
  the old 7-service root compose to `legacy/stray-root/`.
- `run_release_gate.py` no longer scans archived paths.

### T7 â€” Pilot
- Added a non-engineering execution checklist (owner/date/artifact) to
  `docs/pilot/real_kid_pilot_protocol.md`; cohort aligned to 6â€“10 students, Grades 2â€“4.

### T8 â€” Docs synced
- Container topology, harness filenames (`golden_verifier.py`,
  `adversarial_evaluator.py`), OCR status, and test counts updated.
- Absolute `file:///e:/...` and `file:///d:/...` link roots converted to repo-relative
  links across `README.md` and `docs/**`.

---

## 4. Deferred (explicit, out of MVP)

1. Worksheet OCR (Phase 4): needs a local VLM, the BE-11 prompt-injection sanitizer,
   and a handwriting/lighting stress test before it can be claimed.
2. Full Khmer NLP (v2.2): unspaced tokenization, natively authored parallel prompts,
   MoEYS textbook ingestion, Khmer word-problem parser.
3. Classroom pilot execution (protocol and checklist ready; no code work left).

---

## 5. Residual risks

- **LLM provider configuration is still developer-local.** `backend/.env` points at a
  cloud Ollama endpoint. Tests are pinned to `mock`, but a production run inherits
  whatever `.env` contains; set it to `http://localhost:11434` for the offline promise.
- **Database integration is environment-dependent.** `test_api_get_session` tolerates an
  unavailable database (persistence logs an error and the in-memory path serves the
  request), but a live Postgres is needed to verify *persistence*, not just retrieval.
- **CI backend coverage is still a subset.** Local full-suite proof is green (651), but
  CI currently runs the NLU/Socratic subset; expanding it requires pinned model/data
  availability in the runner.
- **No commit was created.** All changes are in the working tree on `chesda`.
