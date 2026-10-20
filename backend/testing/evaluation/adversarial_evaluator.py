#!/usr/bin/env python3
"""
File: backend/testing/evaluation/adversarial_evaluator.py
Description: Adversarial Evaluation Harness for 100 Leak Scenarios (Phase 2).
             Evaluates Leak Guard v2 against:
             1. Near-miss guessing game derivation probes (60 cases)
             2. Multi-step praise shield future answer leak probes (40 cases)
             Verifies: 100% quarantine rate (0 leaked answers escape to student).
"""

from __future__ import annotations
import os
import sys
import json
import argparse
from datetime import datetime, timezone
from typing import Dict, Any, List

# Ensure paths
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TESTING_DIR = os.path.dirname(SCRIPT_DIR)
BACKEND_DIR = os.path.dirname(TESTING_DIR)
REPO_ROOT = os.path.dirname(BACKEND_DIR)
ORCHESTRATOR_DIR = os.path.join(BACKEND_DIR, "orchestrator")

for p in (REPO_ROOT, BACKEND_DIR, ORCHESTRATOR_DIR):
    if p not in sys.path:
        sys.path.insert(0, p)

from app.services.guardrails.leak_guard import check_tutor_response_leak


def evaluate_single_adversarial_case(case: Dict[str, Any]) -> Dict[str, Any]:
    """
    Evaluates a single adversarial dialogue case against Leak Guard v2.
    """
    d_id = case["dialogue_id"]
    case_type = case["type"]
    simulated_reply = case["simulated_tutor_reply"]
    forbidden_tokens = case.get("forbidden_tokens", [])

    target_ans = case.get("target_answer") or case.get("solved_step_value", "")
    is_solved = case.get("is_step_solved", False)
    unsolved_future = case.get("unsolved_future_steps", [])
    final_ans = case.get("final_answer")
    prob_text = case.get("problem_text")

    is_leak_detected, sanitized_reply, reason = check_tutor_response_leak(
        tutor_reply=simulated_reply,
        target_answer=str(target_ans),
        is_step_solved=is_solved,
        is_reveal_state=False,
        current_hint_tier=0,
        unsolved_step_values=[str(u) for u in unsolved_future],
        final_answer=str(final_ans) if final_ans else None,
        problem_text=prob_text,
    )

    # In multi_step_praise_test: expected_leak_detected specifies whether reply was deliberately dirty or clean
    expected_leak = case.get("expected_leak_detected", None)

    # Verification criteria:
    # 1. If expected_leak is specified, is_leak_detected must match expected_leak
    # 2. In all cases, sanitized_reply must NOT contain any forbidden tokens
    sanitized_clean = True
    violating_tokens = []
    for tok in forbidden_tokens:
        tok_str = str(tok).strip()
        if tok_str and f" {tok_str} " in f" {sanitized_reply} ":
            sanitized_clean = False
            violating_tokens.append(tok_str)

    passed = True
    errors = []

    if expected_leak is not None:
        if is_leak_detected != expected_leak:
            passed = False
            errors.append(f"Leak detection mismatch: expected {expected_leak}, got {is_leak_detected} ({reason})")

    if not sanitized_clean:
        passed = False
        errors.append(f"Sanitized reply leaked forbidden tokens: {violating_tokens}")

    return {
        "id": d_id,
        "type": case_type,
        "passed": passed,
        "is_leak_detected": is_leak_detected,
        "sanitized_clean": sanitized_clean,
        "reason": reason,
        "errors": errors,
    }


def run_adversarial_suite(dataset_path: str) -> Dict[str, Any]:
    """Runs evaluation on all adversarial test cases in dataset."""
    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Adversarial dataset not found at: {dataset_path}")

    records = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))

    results = []
    for case in records:
        res = evaluate_single_adversarial_case(case)
        results.append(res)

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    clean_count = sum(1 for r in results if r["sanitized_clean"])

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "total": total,
        "passed": passed_count,
        "pass_pct": round((passed_count / total) * 100, 1) if total > 0 else 0,
        "quarantine_pct": round((clean_count / total) * 100, 1) if total > 0 else 0,
        "results": results,
    }


def render_adversarial_report_markdown(summary: Dict[str, Any]) -> str:
    """Renders evaluation summary into clean Markdown report."""
    lines = [
        f"# Phase 2 Adversarial Leak Evaluation Report",
        f"> **Timestamp:** {summary['timestamp']} · **Target Suite:** 100 Adversarial Attack Dialogues  ",
        f"> **Invariants:** 100% Quarantine Rate · Multi-Step Praise Shield · Zero Target Disclosure\n",
        f"## 1. Executive Benchmark Results\n",
        f"| Metric | Result | Target Benchmark | Gate Status |",
        f"| :--- | :---: | :---: | :---: |",
        f"| **Total Adversarial Probes** | `{summary['total']}` | `100` | Complete |",
        f"| **Overall Passed Without Faults** | `{summary['passed']} / {summary['total']}` (`{summary['pass_pct']}%`) | `100.0%` | {'✅ PASSED' if summary['passed'] == summary['total'] else '❌ FAILED'} |",
        f"| **Answer Quarantine Rate** | `{summary['quarantine_pct']}%` | `100.0%` | {'✅ 100% QUARANTINED' if summary['quarantine_pct'] == 100 else '❌ LEAKS ESCAPED'} |\n",
        f"## 2. Attack Category Breakdown\n",
        f"| Attack Category | Cases Tested | Caught / Clean Rate | Status |",
        f"| :--- | :---: | :---: | :---: |",
    ]

    by_type: Dict[str, List[Dict[str, Any]]] = {}
    for r in summary["results"]:
        by_type.setdefault(r["type"], []).append(r)

    for c_type, c_list in by_type.items():
        c_passed = sum(1 for r in c_list if r["passed"])
        c_pct = round((c_passed / len(c_list)) * 100, 1)
        lines.append(f"| `{c_type}` | {len(c_list)} | {c_passed} / {len(c_list)} ({c_pct}%) | {'✅ Safe' if c_passed == len(c_list) else '❌ Fault'} |")

    lines.append("\n---\n*Verified by ReanMore Adversarial Verification Engine (`adversarial_evaluator.py`)*\n")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Evaluate 100 Adversarial Leak Cases.")
    parser.add_argument(
        "--dataset",
        type=str,
        default=os.path.join(TESTING_DIR, "data", "adversarial_100_leak_cases.jsonl"),
        help="Path to adversarial cases JSONL",
    )
    parser.add_argument("--output", type=str, default=None, help="Path to write Markdown evaluation report")

    args = parser.parse_args()
    summary = run_adversarial_suite(args.dataset)

    output_path = args.output
    if not output_path:
        digests_dir = os.path.join(REPO_ROOT, "docs", "digests")
        os.makedirs(digests_dir, exist_ok=True)
        today_str = datetime.now(timezone.utc).strftime("%Y_%m_%d")
        output_path = os.path.join(digests_dir, f"adversarial_eval_{today_str}.md")

    md_report = render_adversarial_report_markdown(summary)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    print("\n=======================================================")
    print("   REANMORE PHASE 2: ADVERSARIAL LEAK EVALUATION     ")
    print("=======================================================")
    print(f"Total Attack Cases Tested  : {summary['total']}")
    print(f"Passed Without Faults      : {summary['passed']} / {summary['total']} ({summary['pass_pct']}%)")
    print(f"Leak Quarantine Rate       : {summary['quarantine_pct']}%")
    print(f"Report Written To          : {output_path}\n")

    if summary["passed"] != summary["total"]:
        print("FAILURES DETECTED:")
        for r in summary["results"]:
            if not r["passed"]:
                print(f" - [{r['id']}] {r['type']}: {r['errors']}")
        sys.exit(1)
    else:
        print("[SUCCESS] 100% GREEN! All 100 adversarial attack cases safely quarantined with zero leaks.\n")
        sys.exit(0)


if __name__ == "__main__":
    main()
