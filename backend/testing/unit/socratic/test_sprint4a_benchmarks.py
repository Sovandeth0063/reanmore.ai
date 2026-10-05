"""
File: backend/testing/unit/socratic/test_sprint4a_benchmarks.py
Description: Validates the integrity, schema, and label distribution of the 3 golden
             benchmark suites created in Task 4a.1. Also tests Wilson score 95% CI.
"""

import json
import math
from pathlib import Path
import pytest

DATA_DIR = Path(__file__).parent.parent.parent / "data"


def wilson_score_interval(successes: int, total: int, z: float = 1.96) -> tuple[float, float]:
    """Computes Wilson score 95% confidence interval for binomial proportion."""
    if total == 0:
        return 0.0, 0.0
    p = successes / total
    denom = 1 + (z ** 2) / total
    center = (p + (z ** 2) / (2 * total)) / denom
    margin = (z * math.sqrt((p * (1 - p) / total) + (z ** 2) / (4 * (total ** 2)))) / denom
    lower = max(0.0, center - margin)
    upper = min(1.0, center + margin)
    return lower, upper


def test_safety_adversarial_benchmark_integrity():
    file_path = DATA_DIR / "safety_adversarial_benchmark.jsonl"
    assert file_path.exists(), f"Missing {file_path}"
    
    items = []
    ids = set()
    tier_counts = {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            assert "id" in item, f"Missing id at line {line_no}"
            assert item["id"] not in ids, f"Duplicate id {item['id']}"
            ids.add(item["id"])
            assert "text" in item and len(item["text"]) > 0
            assert "expected_tier" in item
            assert "is_safety_violation" in item
            assert "category" in item
            assert "language" in item
            items.append(item)
            tier_counts[item["expected_tier"]] = tier_counts.get(item["expected_tier"], 0) + 1

    assert len(items) == 250
    # Check expected categories
    assert tier_counts.get("TIER2_CHILD_ABUSE", 0) == 50
    assert tier_counts.get("TIER2_SELF_HARM", 0) == 50
    assert tier_counts.get("TIER2_IMMEDIATE_DANGER", 0) == 50
    assert (tier_counts.get("TIER1_EXAM_ANXIETY", 0) + tier_counts.get("TIER0_SAFE", 0)) == 100


def test_leak_adversarial_benchmark_integrity():
    file_path = DATA_DIR / "leak_adversarial_benchmark.jsonl"
    assert file_path.exists(), f"Missing {file_path}"
    
    items = []
    dialogue_ids = set()
    type_counts = {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            assert "dialogue_id" in item, f"Missing dialogue_id at line {line_no}"
            assert item["dialogue_id"] not in dialogue_ids, f"Duplicate id {item['dialogue_id']}"
            dialogue_ids.add(item["dialogue_id"])
            assert "type" in item
            assert "step_id" in item
            assert "forbidden_tokens" in item and len(item["forbidden_tokens"]) > 0
            items.append(item)
            type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1

    assert len(items) == 120
    assert type_counts.get("near_miss_derivation_probe", 0) == 60
    assert type_counts.get("multi_step_praise_test", 0) == 60


def test_grader_golden_benchmark_integrity():
    file_path = DATA_DIR / "grader_golden_benchmark.jsonl"
    assert file_path.exists(), f"Missing {file_path}"
    
    items = []
    ids = set()
    type_counts = {}
    
    with open(file_path, "r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            item = json.loads(line)
            assert "id" in item, f"Missing id at line {line_no}"
            assert item["id"] not in ids, f"Duplicate id {item['id']}"
            ids.add(item["id"])
            assert "student_input" in item
            assert "expected_target" in item
            assert "type" in item
            items.append(item)
            type_counts[item["type"]] = type_counts.get(item["type"], 0) + 1

    assert len(items) == 250
    # Ensure all major types represented
    assert "integer" in type_counts
    assert "number_word" in type_counts
    assert any("comma" in t for t in type_counts)


def test_wilson_confidence_interval():
    # 100% on 200 items
    lower, upper = wilson_score_interval(200, 200)
    assert lower > 0.97
    assert upper == 1.0

    # 50% on 100 items
    lower, upper = wilson_score_interval(50, 100)
    assert 0.39 < lower < 0.41
    assert 0.59 < upper < 0.61
