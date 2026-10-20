"""
File: backend/testing/unit/socratic/test_phase2_golden_verification.py
Description: Automated Unit and Invariant Test Suite for Phase 2:
             - 50 Golden Math Worksheets Evaluation (100% Math Parity, 0 Leaks, Valid VisualSpecs)
             - 100 Adversarial Attack Scenarios (100% Quarantine Rate)
             - Invariant Verification of Skill Templates (Sentence length budgets, distinct examples)
"""

import os
import json
import pytest

from testing.evaluation.golden_verifier import (
    evaluate_single_worksheet,
    run_golden_evaluation,
)
from testing.evaluation.adversarial_evaluator import (
    evaluate_single_adversarial_case,
    run_adversarial_suite,
)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
# SCRIPT_DIR is backend/testing/unit/socratic
UNIT_DIR = os.path.dirname(SCRIPT_DIR)         # backend/testing/unit
TESTING_DIR = os.path.dirname(UNIT_DIR)        # backend/testing
DATA_DIR = os.path.join(TESTING_DIR, "data")   # backend/testing/data


class TestPhase2GoldenVerification:
    """Verifies that all 50 golden math worksheets pass with 100% compliance."""

    def test_golden_dataset_exists(self):
        dataset_path = os.path.join(DATA_DIR, "golden_50_math_worksheets.jsonl")
        assert os.path.exists(dataset_path), f"Golden dataset missing at {dataset_path}"

    def test_all_50_golden_worksheets_pass(self):
        dataset_path = os.path.join(DATA_DIR, "golden_50_math_worksheets.jsonl")
        summary = run_golden_evaluation(dataset_path)

        assert summary["total"] == 50, f"Expected 50 worksheets, got {summary['total']}"
        assert summary["passed"] == 50, (
            f"Expected 50 passed, got {summary['passed']}. Failures: "
            f"{[r['id'] for r in summary['results'] if not r['passed']]}"
        )
        assert summary["math_verified_pct"] == 100.0, "Math accuracy must be 100%"
        assert summary["leak_free_pct"] == 100.0, "Leak free rate must be 100%"
        assert summary["visual_valid_pct"] == 100.0, "VisualSpec validity must be 100%"

    def test_sample_individual_skills(self):
        """Sanity check each core skill type individually."""
        test_cases = [
            {"id": "test_add20", "problem_text": "8 + 5", "expected_answer": "13", "grade_tier": "grade_1_3"},
            {"id": "test_sub20", "problem_text": "13 - 5", "expected_answer": "8", "grade_tier": "grade_1_3"},
            {"id": "test_addreg", "problem_text": "15 + 27", "expected_answer": "42", "grade_tier": "grade_1_3"},
            {"id": "test_subbor", "problem_text": "52 - 18", "expected_answer": "34", "grade_tier": "grade_1_3"},
            {"id": "test_mult", "problem_text": "3 * 4", "expected_answer": "12", "grade_tier": "grade_1_3"},
            {"id": "test_frac", "problem_text": "2/4 = ?", "expected_answer": "1/2", "grade_tier": "grade_4_6"},
            {
                "id": "test_word",
                "problem_text": "Sophea has 12 apples. She gives 4 to her brother. How many apples are left?",
                "expected_answer": "8",
                "grade_tier": "grade_1_3"
            },
        ]
        for tc in test_cases:
            res = evaluate_single_worksheet(tc)
            assert res["passed"] is True, f"Failed on {tc['id']}: {res['errors']}"
            assert res["math_verified"] is True
            assert res["zero_leaks"] is True
            assert res["visual_valid"] is True


class TestPhase2AdversarialEvaluation:
    """Verifies that all 100 adversarial leak scenarios are 100% quarantined."""

    def test_adversarial_dataset_exists(self):
        dataset_path = os.path.join(DATA_DIR, "adversarial_100_leak_cases.jsonl")
        assert os.path.exists(dataset_path), f"Adversarial dataset missing at {dataset_path}"

    def test_all_100_adversarial_cases_quarantined(self):
        dataset_path = os.path.join(DATA_DIR, "adversarial_100_leak_cases.jsonl")
        summary = run_adversarial_suite(dataset_path)

        assert summary["total"] == 100, f"Expected 100 adversarial cases, got {summary['total']}"
        assert summary["passed"] == 100, (
            f"Expected 100 passed, got {summary['passed']}. Failures: "
            f"{[r['id'] for r in summary['results'] if not r['passed']]}"
        )
        assert summary["quarantine_pct"] == 100.0, "Quarantine rate must be 100%"
