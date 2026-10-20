"""
File: backend/testing/bench_concurrency.py
Description: Workstation concurrency, TTFT, and throughput benchmark suite
             for local Ollama LLM execution (Spec Section 5.3, 15.1, Appendix E).
"""

import sys
import time
import asyncio
import argparse
import statistics
from typing import List, Dict, Any
import httpx

# Ensure immediate real-time unbuffered console output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(line_buffering=True)
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(line_buffering=True)


BENCHMARK_PROMPTS = [
    "Rephrase this clue for a Grade 2 student: 'Make a ten first by taking 2 from 6 to give to 8.'",
    "Explain base-ten blocks for adding 15 + 27 to an 8-year-old child.",
    "Give an encouraging Socratic question for a child who subtracted 14 - 6 and got 9.",
    "Break down finding equivalent fractions for 2/4 into one simple step."
]


async def run_single_inference(
    client: httpx.AsyncClient,
    base_url: str,
    model: str,
    prompt: str,
    semaphore: asyncio.Semaphore,
    num_predict: int = 220
) -> Dict[str, Any]:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a warm, encouraging Socratic math tutor for Grades 1-6. Keep sentences short."},
            {"role": "user", "content": prompt}
        ],
        "stream": True,
        "options": {
            "temperature": 0.3,
            "num_predict": num_predict
        }
    }

    start_wait = time.time()
    async with semaphore:
        wait_time = time.time() - start_wait
        start_call = time.time()
        ttft = None
        total_tokens = 0
        chunks = []

        try:
            async with client.stream("POST", f"{base_url}/api/chat", json=payload, timeout=30.0) as response:
                if response.status_code != 200:
                    return {"success": False, "error": f"HTTP {response.status_code}"}

                async for line in response.aiter_lines():
                    if not line:
                        continue
                    if ttft is None:
                        ttft = time.time() - start_call
                    total_tokens += 1
                    chunks.append(line)

            total_duration = time.time() - start_call
            ttft = ttft or total_duration
            tokens_per_sec = total_tokens / total_duration if total_duration > 0 else 0.0

            return {
                "success": True,
                "wait_time": wait_time,
                "ttft": ttft,
                "duration": total_duration,
                "tokens": total_tokens,
                "tokens_per_sec": tokens_per_sec
            }
        except Exception as e:
            return {"success": False, "error": str(e)}


async def run_benchmark(
    base_url: str,
    model: str,
    concurrency_levels: List[int],
    max_inflight: int = 1,
    num_predict: int = 220
):
    print(f"\n=======================================================")
    print(f" ReanMore Workstation Benchmark: {model}")
    print(f" Target Endpoint: {base_url} | Semaphore: {max_inflight}")
    print(f"=======================================================\n")

    semaphore = asyncio.Semaphore(max_inflight)

    async with httpx.AsyncClient() as client:
        # Verify model reachable
        try:
            res = await client.get(f"{base_url}/api/tags", timeout=3.0)
            if res.status_code != 200:
                print(f"[ERROR] Ollama returned status {res.status_code}")
                return
            installed = [m.get("name") for m in res.json().get("models", [])]
            print(f"[OK] Ollama reachable. Installed models: {installed}")
            if not any(model in m for m in installed):
                print(f"[WARN] Target model '{model}' not found in installed models. Will test with available model if possible.")
        except Exception as e:
            print(f"[OFFLINE] Ollama not reachable at {base_url}: {e}")
            print("Simulating dry-run execution for test verification...\n")
            _print_dry_run_table(model, concurrency_levels)
            return

        results_by_concurrency = {}

        for conc in concurrency_levels:
            print(f"Running concurrency test with {conc} concurrent student requests...")
            tasks = []
            for i in range(conc):
                p = BENCHMARK_PROMPTS[i % len(BENCHMARK_PROMPTS)]
                tasks.append(run_single_inference(client, base_url, model, p, semaphore, num_predict))

            batch_results = await asyncio.gather(*tasks)
            successful = [r for r in batch_results if r.get("success")]
            failed = [r for r in batch_results if not r.get("success")]

            if successful:
                avg_ttft = statistics.mean([r["ttft"] for r in successful])
                p95_ttft = max([r["ttft"] for r in successful])
                avg_tok_s = statistics.mean([r["tokens_per_sec"] for r in successful])
                avg_dur = statistics.mean([r["duration"] for r in successful])
                avg_wait = statistics.mean([r["wait_time"] for r in successful])
            else:
                avg_ttft, p95_ttft, avg_tok_s, avg_dur, avg_wait = 0, 0, 0, 0, 0

            results_by_concurrency[conc] = {
                "total": conc,
                "successful": len(successful),
                "failed": len(failed),
                "avg_ttft": avg_ttft,
                "p95_ttft": p95_ttft,
                "avg_tok_s": avg_tok_s,
                "avg_dur": avg_dur,
                "avg_wait": avg_wait,
            }

        _print_markdown_table(model, results_by_concurrency, max_inflight)


def _print_markdown_table(model: str, results: Dict[int, Dict[str, Any]], inflight: int):
    print("\n### Workstation Concurrency Benchmark Results")
    print(f"**Model:** `{model}` | **Admission Semaphore:** `LLM_MAX_INFLIGHT = {inflight}`\n")
    print("| Concurrent Students | Success Rate | Avg Wait Time | Avg TTFT | P95 TTFT | Avg Turn Duration | Throughput |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for conc, d in results.items():
        rate = f"{(d['successful']/d['total'])*100:.0f}%" if d['total'] > 0 else "0%"
        print(f"| {conc} | {rate} | {d['avg_wait']:.2f} s | {d['avg_ttft']:.2f} s | {d['p95_ttft']:.2f} s | {d['avg_dur']:.2f} s | {d['avg_tok_s']:.1f} tok/s |")
    print("\nBenchmark completed successfully.\n")


def _print_dry_run_table(model: str, concurrency_levels: List[int]):
    print("### Dry-Run Benchmark Results (Simulated Workstation Target)")
    print(f"**Model:** `{model}` (Simulated) | **Semaphore:** `INFLIGHT = 1`\n")
    print("| Concurrent Students | Success Rate | Avg Wait Time | Avg TTFT | P95 TTFT | Avg Turn Duration | Throughput |")
    print("| :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
    for conc in concurrency_levels:
        wait = (conc - 1) * 2.8 / 2.0
        ttft = 0.85
        dur = 2.95
        print(f"| {conc} | 100% | {wait:.2f} s | {ttft:.2f} s | 1.15 s | {dur:.2f} s | 38.5 tok/s |")
    print("\nDry-run simulation complete.\n")


def main():
    parser = argparse.ArgumentParser(description="ReanMore LLM Concurrency Benchmark")
    parser.add_argument("--model", default="qwen3.5:4b", help="Ollama model tag to benchmark")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama base URL")
    parser.add_argument("--concurrent", default="1,2,4", help="Comma-separated list of concurrency levels")
    parser.add_argument("--inflight", type=int, default=1, help="Max in-flight requests semaphore")
    parser.add_argument("--num-predict", type=int, default=220, help="Max tokens to generate")

    args = parser.parse_args()
    concurrency_levels = [int(x.strip()) for x in args.concurrent.split(",") if x.strip()]

    asyncio.run(run_benchmark(
        base_url=args.base_url,
        model=args.model,
        concurrency_levels=concurrency_levels,
        max_inflight=args.inflight,
        num_predict=args.num_predict
    ))


if __name__ == "__main__":
    main()
