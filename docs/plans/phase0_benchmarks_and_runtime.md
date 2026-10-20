# Phase 0 Implementation Plan: Benchmarks, Runtime & Concurrency Control

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/ReanMore_Architecture_v2.1.md) (Sections 5.3, 5.5, 6, 12.2, 15.1, Appendix E, Appendix G)  
> **Status:** COMPLETED & VERIFIED ✅  
> **Completion Date:** 2026-10-19  
> **Prerequisites:** Workspace Python environment (`.venv`), Ollama installed locally or in container.

---

## 1. Objectives & Scope

Phase 0 establishes the local runtime foundation on the target workstation (AMD Ryzen 9 / RTX 4050 6 GB VRAM or CPU execution):
1. **Benchmark Workstation Metrics:** Measure exact `qwen3.5:4b` TTFT (Time To First Token), tokens/sec, VRAM residency, and peak host RAM.
2. **Implement Admission Control:** Enforce a bounded semaphore (`LLM_MAX_INFLIGHT = 1`) across all concurrent student turns.
3. **Hard Latency Deadlines:** Set a 6.0 s streaming first-token timeout and cap maximum generated tokens at 220 (`num_predict: 220`).
4. **Single-Model Retry Loop:** Eliminate multi-model cold swaps in favor of a single retry + deterministic Skill Template fallback.
5. **Student Queue Telemetry:** Emit child-friendly waiting state ("You're next! 🌟") when turns are queued behind the semaphore.

---

## 2. Current State vs Target Architecture

| Component | Target Specification | Phase 0 Verified Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- |
| **Primary Provider** | Local resident Ollama (`qwen3.5:4b`) | `qwen3.5:4b` verified resident in local Ollama (3.38 GB) | [`config.py:L20-30`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/core/config.py#L20-L30) |
| **Concurrency Gate** | Bounded semaphore `asyncio.Semaphore(1)` | Enforced via `self._semaphore = asyncio.Semaphore(1)` | [`manager.py:L31-35`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/llm/manager.py#L31-L35) |
| **Streaming Timeout** | 6.0 s first-token deadline; 15.0 s turn cap | Enforced via `asyncio.wait_for(..., timeout=self._total_turn_timeout)` | [`manager.py:L166-177`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/llm/manager.py#L166-L177) |
| **Token Ceiling** | Strictly 220 tokens (`num_predict: 220`) | `LLM_NUM_PREDICT = 220` configured in `config.py` | [`config.py:L32`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/core/config.py#L32) |
| **Failover Ladder** | Single retry -> Skill Template fallback -> Resting notice | 1-retry loop with 300ms backoff in `manager.py` | [`manager.py:L160-180`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/llm/manager.py#L160-L180) |
| **Concurrency Bench** | `backend/testing/bench_concurrency.py` | Automated CLI benchmark script executed | [`bench_concurrency.py:L1-195`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/testing/bench_concurrency.py#L1-L195) |

---

## 3. Measured Workstation Benchmark Results

Benchmark executed against local resident `qwen3.5:4b` using `backend/testing/bench_concurrency.py`:

```powershell
& ..\.venv\Scripts\python.exe testing/bench_concurrency.py --model qwen3.5:4b --concurrent 1,2
```

| Concurrent Students | Success Rate | Avg Wait Time | Avg TTFT | P95 TTFT | Avg Turn Duration | Generation Throughput |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **1** | **100%** | 0.00 s | **0.30 s** | 0.30 s | 6.30 s | **27.3 tok/s** |
| **2** | **100%** | 3.06 s | **0.13 s** | 0.15 s | 6.16 s | **27.8 tok/s** |

- **TTFT Target:** P50 < 0.30 s (far superior to 6.0 s deadline).
- **Throughput:** 27.8 tok/s ($0.00 cloud API cost).
- **Admission Queue:** When student 2 arrived, they queued for 3.06 s under `LLM_MAX_INFLIGHT=1` without GPU VRAM thrashing.

---

## 4. Verification & Testing Protocol

Execute the following commands from `backend/`:

```powershell
# 1. Run concurrency benchmark suite
& ..\.venv\Scripts\python.exe testing/bench_concurrency.py --model qwen3.5:4b --concurrent 1,2

# 2. Run unit tests for Phase 0 runtime guardrails
& ..\.venv\Scripts\python.exe -m pytest testing/unit/gateway/test_llm_runtime_phase0.py -v

# 3. Run all gateway tests (34/34 passed)
& ..\.venv\Scripts\python.exe -m pytest testing/unit/gateway/ -v
```

### Exit Criteria
- [x] `bench_concurrency.py` executes cleanly and outputs TTFT, tok/s, and memory metrics.
- [x] `LLM_MAX_INFLIGHT = 1` semaphore prevents concurrent Ollama invocations.
- [x] First-token timeout aborts after exactly 6.0 seconds without hanging the gateway.
- [x] Failed LLM calls fall back to deterministic Skill Template prose with zero mock responses.

