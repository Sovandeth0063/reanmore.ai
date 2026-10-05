"""
Unit tests for Sprint 3 (Contextual Cache, Event Summary & CI Gates).
Tests:
  1. Contextual LRU Cache (Task 3.1)
  2. Structured Event-Based Rolling Summary (Task 3.2)
  3. Automated Regression CI Benchmark Evaluator (Task 3.3)
"""

import os
import sys
import time
import threading
# pyrefly: ignore [missing-import]
import pytest

# Ensure repo root and orchestrator are on sys.path
def _find_repo_root():
    cur = os.path.abspath(os.path.dirname(__file__))
    while cur and not os.path.exists(os.path.join(cur, "orchestrator")):
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return cur

BASE_DIR = _find_repo_root()
ORCHESTRATOR_DIR = os.path.join(BASE_DIR, "orchestrator")
for _p in (BASE_DIR, ORCHESTRATOR_DIR):
    if _p not in sys.path:
        sys.path.insert(0, _p)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orchestrator")))

# pyrefly: ignore [missing-import]
from app.services.nlu.context_cache import (
    ContextCache,
    generate_context_cache_key,
    is_cacheable_intent,
)
# pyrefly: ignore [missing-import]
from app.services.socratic.event_summary import (
    RollingSessionSummary,
    StepEvent,
)
# pyrefly: ignore [missing-import]
from testing.tools.run_intent_benchmark import evaluate_benchmark, BenchmarkReport


class TestContextualLruCache:
    """Task 3.1: Contextual LRU Cache tests."""

    def test_cache_key_generation_and_normalization(self):
        key1 = generate_context_cache_key("  What is photosynthesis?  ", "concept", "SCIENCE", "EN")
        key2 = generate_context_cache_key("what is photosynthesis?", "concept", "science", "en")
        assert key1 == key2, "Cache key must normalize casing and whitespace"
        assert len(key1) == 64, "Key must be a 64-character SHA-256 hex string"

    def test_cache_intent_gating(self):
        # Cacheable intents
        assert is_cacheable_intent("OFF_TOPIC_DEFLECTED") is True
        assert is_cacheable_intent("CHITCHAT") is True
        assert is_cacheable_intent("CONCEPT_INQUIRY") is True

        # Non-cacheable intents (must bypass cache)
        assert is_cacheable_intent("STEP_ANSWER_ATTEMPT") is False
        assert is_cacheable_intent("REQUEST_HINT") is False
        assert is_cacheable_intent("SAFETY_CONCERN") is False
        assert is_cacheable_intent("ANSWER_DEMAND") is False
        assert is_cacheable_intent("UNCLEAR") is False
        assert is_cacheable_intent(None) is False

    def test_cache_set_and_get(self):
        cache = ContextCache(max_size=10, default_ttl_seconds=60)
        key = generate_context_cache_key("hello", "none", "general", "en")
        
        stored = cache.set(key, {"reply": "Hi there!"}, intent="CHITCHAT")
        assert stored is True
        
        cached_val = cache.get(key)
        assert cached_val == {"reply": "Hi there!"}

    def test_cache_bypasses_non_cacheable_intent(self):
        cache = ContextCache(max_size=10)
        key = generate_context_cache_key("15", "arithmetic", "math", "en")
        
        stored = cache.set(key, {"answer": 15}, intent="STEP_ANSWER_ATTEMPT")
        assert stored is False, "Answer attempts must be bypassed by the cache"
        assert cache.get(key) is None
        stats = cache.stats()
        assert stats["bypasses"] == 1

    def test_lru_capacity_eviction(self):
        cache = ContextCache(max_size=3)
        for i in range(1, 4):
            k = f"key_{i}"
            cache.set(k, f"val_{i}")
        
        assert cache.size() == 3
        # Access key_1 to make key_2 the least-recently used
        cache.get("key_1")
        
        # Add key_4, which must evict key_2
        cache.set("key_4", "val_4")
        assert cache.get("key_2") is None, "Least recently used key_2 should have been evicted"
        assert cache.get("key_1") == "val_1"
        assert cache.get("key_4") == "val_4"
        assert cache.stats()["evictions"] == 1

    def test_ttl_expiry(self):
        cache = ContextCache(max_size=5, default_ttl_seconds=1)
        cache.set("temp_key", "temp_value", ttl_seconds=1)
        assert cache.get("temp_key") == "temp_value"
        
        # Sleep past TTL
        time.sleep(1.05)
        assert cache.get("temp_key") is None, "Expired entry must return None"

    def test_thread_safety(self):
        cache = ContextCache(max_size=100)
        
        def worker(worker_id: int):
            for i in range(50):
                k = f"k_{worker_id}_{i}"
                cache.set(k, i)
                val = cache.get(k)
                assert val == i or val is None

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert cache.size() <= 100


class TestStructuredEventRollingSummary:
    """Task 3.2: Structured Event-Based Rolling Summary tests."""

    def test_record_attempt_and_outcomes(self):
        summary = RollingSessionSummary(session_id="test_sess_01", subject="math", grade_level=2)
        
        # 1st wrong attempt
        ev1 = summary.record_attempt(step_number=1, is_correct=False, step_type="addition", objective="Add 5 + 3")
        assert ev1.attempt_count == 1
        assert ev1.outcome == "attempt_failed"
        assert summary.active_step_number == 1

        # 2nd attempt correct
        ev2 = summary.record_attempt(step_number=1, is_correct=True)
        assert ev2.attempt_count == 2
        assert ev2.outcome == "step_completed"
        assert summary.active_step_number == 2

    def test_record_hints_and_tiers(self):
        summary = RollingSessionSummary(session_id="test_sess_02")
        summary.record_hint(step_number=2, hint_tier=1, hint_label="tier1_socratic_clue")
        summary.record_hint(step_number=2, hint_tier=2, hint_label="tier2_step_breakdown")
        
        ev = summary.get_or_create_event(2)
        assert ev.hints_given == ["tier1_socratic_clue", "tier2_step_breakdown"]
        assert ev.outcome == "hint_requested"

    def test_bounding_max_retained_events(self):
        summary = RollingSessionSummary(session_id="test_sess_03", max_retained_events=3)
        for s in range(1, 6):
            summary.record_attempt(step_number=s, is_correct=True, objective=f"Step {s}")

        assert len(summary.recent_events) == 3
        step_numbers = [e.step_number for e in summary.recent_events]
        assert step_numbers == [3, 4, 5], "Must prune to the most recent 3 events"

    def test_xml_context_formatting_and_escaping(self):
        summary = RollingSessionSummary(session_id="test_sess_04", subject="science", grade_level=3)
        summary.record_attempt(step_number=1, is_correct=True, step_type="concept", objective="Explain <chlorophyll>")
        summary.set_last_tutor_prompt("Is 15 > 10?")
        
        xml = summary.to_xml_context()
        assert "<session_events active_step=" in xml
        assert '<objective>Explain &lt;chlorophyll&gt;</objective>' in xml
        assert '<last_tutor_prompt>Is 15 &gt; 10?</last_tutor_prompt>' in xml
        assert "</session_events>" in xml

    def test_state_serialization_roundtrip(self):
        summary = RollingSessionSummary(session_id="test_sess_05", subject="math", grade_level=4)
        summary.record_attempt(step_number=1, is_correct=True)
        summary.record_hint(step_number=2, hint_tier=1)
        summary.set_last_tutor_prompt("What is half of 20?")

        data_dict = summary.to_dict()
        restored = RollingSessionSummary.from_dict(data_dict)

        assert restored.session_id == summary.session_id
        assert restored.subject == summary.subject
        assert restored.grade_level == summary.grade_level
        assert restored.last_tutor_prompt == "What is half of 20?"
        assert len(restored.recent_events) == 2


class TestCiBenchmarkRunnerAndRegressionGates:
    """Task 3.3: Automated Regression CI Runner tests against benchmark corpus."""

    def test_benchmark_runner_evaluates_dev_split(self):
        report: BenchmarkReport = evaluate_benchmark(split="dev")
        assert report.split == "dev"
        assert report.total_samples == 200
        assert report.passed_all_gates is True
        assert report.khmer_accuracy >= 90.0
        assert report.english_accuracy >= 94.0
        assert report.khmenglish_accuracy >= 88.0
        assert report.critical_safety_recall == 100.0
        assert report.safety_fp_rate < 1.0
        assert report.avg_latency_ms < 2.0

    def test_benchmark_runner_evaluates_held_out_test_split(self):
        report: BenchmarkReport = evaluate_benchmark(split="test")
        assert report.split == "test"
        assert report.total_samples == 300
        assert report.passed_all_gates is True
        assert report.khmer_accuracy >= 90.0
        assert report.english_accuracy >= 94.0
        assert report.khmenglish_accuracy >= 88.0
        assert report.critical_safety_recall == 100.0
        assert report.safety_fp_rate < 1.0
        assert report.avg_latency_ms < 2.0
