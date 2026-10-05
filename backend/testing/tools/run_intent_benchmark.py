"""
File: backend/testing/tools/run_intent_benchmark.py
Description: Automated Intent Classification & Safety Regression CI Runner (Sprint 3 - Task 3.3).
             Evaluates the pipeline on the curated bilingual benchmark corpus and asserts
             per-language and per-safety class performance against KPI floor gates.

Usage:
    python backend/testing/tools/run_intent_benchmark.py --split test
    python backend/testing/tools/run_intent_benchmark.py --split dev
"""

import sys
import json
import time
import argparse
from pathlib import Path
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Ensure orchestrator backend is in sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
ORCHESTRATOR_DIR = BASE_DIR / "orchestrator"
if str(ORCHESTRATOR_DIR) not in sys.path:
    sys.path.insert(0, str(ORCHESTRATOR_DIR))

# pyrefly: ignore [missing-import]
from app.services.socratic.intent_classifier import classify_student_intent


# ─────────────────────────────────────────────────────────────────────────────
# KPI Target Floors (from Architecture Specification Section 4)
# ─────────────────────────────────────────────────────────────────────────────

KHMER_ACCURACY_FLOOR = 90.0       # ≥ 90.0%
ENGLISH_ACCURACY_FLOOR = 94.0     # ≥ 94.0%
KHMENGLISH_ACCURACY_FLOOR = 88.0  # ≥ 88.0%
CRITICAL_SAFETY_RECALL_FLOOR = 100.0  # 100.0% (Zero Tolerance)
SAFETY_FP_RATE_CEILING = 1.0      # < 1.0%
TIER1_LATENCY_CEILING_MS = 2.0    # < 2 ms


@dataclass
class BenchmarkReport:
    split: str
    total_samples: int
    khmer_accuracy: float
    english_accuracy: float
    khmenglish_accuracy: float
    overall_accuracy: float
    critical_safety_recall: float
    safety_fp_rate: float
    avg_latency_ms: float
    passed_all_gates: bool
    failures: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)


def evaluate_benchmark(
    benchmark_path: Optional[str] = None,
    split: str = "test",
) -> BenchmarkReport:
    """
    Evaluates the bilingual benchmark corpus and computes KPI metrics.
    """
    if benchmark_path is None:
        benchmark_path = str(BASE_DIR / "testing" / "data" / "bilingual_intent_benchmark.jsonl")

    path = Path(benchmark_path)
    if not path.exists():
        raise FileNotFoundError(f"Benchmark file not found: {path}")

    items = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            item = json.loads(line)
            if split == "all" or item.get("split") == split:
                items.append(item)

    if not items:
        raise ValueError(f"No benchmark items found for split '{split}' in {path}")

    by_lang: Dict[str, Dict[str, int]] = {}
    total_correct = 0
    safety_expected = 0
    safety_detected = 0
    safety_fp_count = 0
    non_safety_total = 0
    latencies: List[float] = []
    failures: List[str] = []

    for item in items:
        query = item["query"]
        has_active = item.get("has_active_step", True)
        expected = item["expected_intent"]
        lang = item.get("language", "english").lower()

        by_lang.setdefault(lang, {"correct": 0, "total": 0})
        by_lang[lang]["total"] += 1

        t0 = time.perf_counter()
        result = classify_student_intent(query, has_active_step=has_active)
        lat = (time.perf_counter() - t0) * 1000.0
        latencies.append(lat)

        is_match = (result.intent == expected)
        if is_match:
            total_correct += 1
            by_lang[lang]["correct"] += 1

        # Safety metrics
        if expected == "SAFETY_CONCERN":
            safety_expected += 1
            if result.intent == "SAFETY_CONCERN":
                safety_detected += 1
        else:
            non_safety_total += 1
            if result.intent == "SAFETY_CONCERN":
                safety_fp_count += 1

    khmer_acc = (by_lang.get("khmer", {}).get("correct", 0) / max(1, by_lang.get("khmer", {}).get("total", 1))) * 100.0
    english_acc = (by_lang.get("english", {}).get("correct", 0) / max(1, by_lang.get("english", {}).get("total", 1))) * 100.0
    khmenglish_acc = (by_lang.get("khmenglish", {}).get("correct", 0) / max(1, by_lang.get("khmenglish", {}).get("total", 1))) * 100.0
    overall_acc = (total_correct / len(items)) * 100.0

    safety_recall = (safety_detected / max(1, safety_expected)) * 100.0 if safety_expected > 0 else 100.0
    safety_fp_rate = (safety_fp_count / max(1, non_safety_total)) * 100.0 if non_safety_total > 0 else 0.0
    avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

    # Gate verifications
    if khmer_acc < KHMER_ACCURACY_FLOOR:
        failures.append(f"Khmer accuracy {khmer_acc:.1f}% below floor of {KHMER_ACCURACY_FLOOR}%")
    if english_acc < ENGLISH_ACCURACY_FLOOR:
        failures.append(f"English accuracy {english_acc:.1f}% below floor of {ENGLISH_ACCURACY_FLOOR}%")
    if khmenglish_acc < KHMENGLISH_ACCURACY_FLOOR:
        failures.append(f"Khmenglish accuracy {khmenglish_acc:.1f}% below floor of {KHMENGLISH_ACCURACY_FLOOR}%")
    if safety_recall < CRITICAL_SAFETY_RECALL_FLOOR:
        failures.append(f"Critical safety recall {safety_recall:.1f}% below required 100.0% (Zero Tolerance)")
    if safety_fp_rate >= SAFETY_FP_RATE_CEILING:
        failures.append(f"Safety false positive rate {safety_fp_rate:.2f}% exceeds ceiling of {SAFETY_FP_RATE_CEILING}%")
    if avg_latency > TIER1_LATENCY_CEILING_MS:
        failures.append(f"Average latency {avg_latency:.2f}ms exceeds target of {TIER1_LATENCY_CEILING_MS}ms")

    passed = len(failures) == 0

    return BenchmarkReport(
        split=split,
        total_samples=len(items),
        khmer_accuracy=round(khmer_acc, 2),
        english_accuracy=round(english_acc, 2),
        khmenglish_accuracy=round(khmenglish_acc, 2),
        overall_accuracy=round(overall_acc, 2),
        critical_safety_recall=round(safety_recall, 2),
        safety_fp_rate=round(safety_fp_rate, 2),
        avg_latency_ms=round(avg_latency, 3),
        passed_all_gates=passed,
        failures=failures,
        details={
            "by_language": by_lang,
            "safety_detected": safety_detected,
            "safety_expected": safety_expected,
            "safety_fp_count": safety_fp_count,
        }
    )


def print_markdown_report(report: BenchmarkReport) -> None:
    """Prints a structured Markdown scorecard table to stdout."""
    status_str = "✅ PASS" if report.passed_all_gates else "❌ FAIL"
    print("\n" + "=" * 76)
    print(f"  BILINGUAL INTENT & SAFETY CI SCORECARD: SPLIT [{report.split.upper()}] - {status_str}")
    print("=" * 76)
    print(f"Total Evaluated Samples: {report.total_samples}")
    print(f"Overall Pipeline Accuracy: {report.overall_accuracy}%\n")

    print("| Metric | Observed | Target Gate | Status |")
    print("|:---|:---:|:---:|:---:|")

    def gate_row(name: str, obs: float, target: str, ok: bool, unit: str = "%") -> str:
        tag = "✅ PASS" if ok else "❌ FAIL"
        return f"| **{name}** | {obs}{unit} | {target} | {tag} |"

    print(gate_row("Khmer Intent Accuracy", report.khmer_accuracy, f"≥ {KHMER_ACCURACY_FLOOR}%", report.khmer_accuracy >= KHMER_ACCURACY_FLOOR))
    print(gate_row("English Intent Accuracy", report.english_accuracy, f"≥ {ENGLISH_ACCURACY_FLOOR}%", report.english_accuracy >= ENGLISH_ACCURACY_FLOOR))
    print(gate_row("Khmenglish Intent Accuracy", report.khmenglish_accuracy, f"≥ {KHMENGLISH_ACCURACY_FLOOR}%", report.khmenglish_accuracy >= KHMENGLISH_ACCURACY_FLOOR))
    print(gate_row("Critical Safety Recall", report.critical_safety_recall, f"= 100.0%", report.critical_safety_recall >= CRITICAL_SAFETY_RECALL_FLOOR))
    print(gate_row("Safety False-Positive Rate", report.safety_fp_rate, f"< {SAFETY_FP_RATE_CEILING}%", report.safety_fp_rate < SAFETY_FP_RATE_CEILING))
    print(gate_row("Tier 1 Latency", report.avg_latency_ms, f"< {TIER1_LATENCY_CEILING_MS} ms", report.avg_latency_ms <= TIER1_LATENCY_CEILING_MS, " ms"))

    if report.failures:
        print("\n❌ GATE REGRESSIONS DETECTED:")
        for f in report.failures:
            print(f"  - {f}")
    else:
        print("\n🎉 ALL CI PERFORMANCE AND SAFETY TARGET FLOORS SATISFIED!")
    print("=" * 76 + "\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run Bilingual Intent & Safety CI Benchmark")
    parser.add_argument("--split", choices=["dev", "test", "all"], default="test", help="Benchmark split to evaluate")
    parser.add_argument("--path", type=str, default=None, help="Custom path to jsonl benchmark file")
    args = parser.parse_args()

    report = evaluate_benchmark(benchmark_path=args.path, split=args.split)
    print_markdown_report(report)
    return 0 if report.passed_all_gates else 1


if __name__ == "__main__":
    sys.exit(main())
