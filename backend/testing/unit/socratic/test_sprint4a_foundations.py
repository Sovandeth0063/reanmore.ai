"""
File: backend/testing/unit/socratic/test_sprint4a_foundations.py
Description: Acceptance test suite for Sprint 4a:
             1. Golden benchmark suites & statistical intervals (Task 4a.1)
             2. Centralized tutoring config verification (Task 4a.2)
             3. Grader order of operations, Khmer numerals, words & commas (Task 4a.3)
             4. Identical non-directional near-miss invariant (Task 4a.4)
             5. Multi-step praise leak shield & token boundaries (Task 4a.5)
             6. Categorical Tier 2 safety split & counselor-first escalation (Task 4a.6)
"""

import os
import sys
import json
import pytest
from pathlib import Path

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
from app.core.tutoring_config import (
    PROXIMITY_FEEDBACK_TOLERANCE,
    MAX_PROXIMITY_FEEDBACK_PER_STEP,
    MAX_ATTEMPTS_BEFORE_REVEAL,
    OCR_CONFIDENCE_THRESHOLD,
    STT_CONFIDENCE_THRESHOLD,
    CHILD_HELPLINE_CAMBODIA,
    CHILD_HELPLINE_VERIFIED_DATE,
    HELPLINE_SOURCE_CHECKED_DATE,
    HELPLINE_WRITTEN_CONFIRMATION_PENDING,
    EMERGENCY_POLICE_CAMBODIA,
    EMERGENCY_AMBULANCE_CAMBODIA,
    EMERGENCY_FIRE_CAMBODIA,
    EMERGENCY_SERVICES_FALLBACK,
    SAFEGUARDING_REVIEW_SLA_MINUTES,
    DEFAULT_SAFEGUARDING_OWNER,
    SAFEGUARDING_PORTAL_URL,
    SAFE_PRAISE_FALLBACK_ENG,
    SAFE_PRAISE_FALLBACK_KHMER,
    NEAR_MISS_FEEDBACK_ENG,
    NEAR_MISS_FEEDBACK_KHMER,
    PROPERTY_QUERY_DEFLECTION_ENG,
    PROPERTY_QUERY_DEFLECTION_KHMER
)
# pyrefly: ignore [missing-import]
from app.services.socratic.validate_answer import (
    validate_student_answer,
    validate_socratic_answer,
    check_property_confirmation_query,
    RevealState,
    VALIDATION_CORRECT,
    VALIDATION_PARTIAL,
    VALIDATION_INCORRECT
)
# pyrefly: ignore [missing-import]
from app.services.socratic.invariants import (
    normalize_student_input,
    extract_raw_input_numeric_tokens,
    verify_number_traceability,
    is_ambiguous_locale_number
)
# pyrefly: ignore [missing-import]
from app.services.socratic.leak_checker import (
    check_tutor_response_leak,
    check_response_for_leaks
)
# pyrefly: ignore [missing-import]
from app.services.guardrails.safety_filter import (
    SafetyFilter,
    SafetyCategory,
    evaluate_safety_tier
)
# pyrefly: ignore [missing-import]
from app.services.guardrails.escalation import (
    dispatch_safety_alert,
    dispatch_escalation_alert,
    get_safeguarding_review_queue,
    clear_safeguarding_review_queue,
    acknowledge_safeguarding_alert,
    check_and_escalate_unacknowledged,
    format_content_free_notification_ping
)


# ─────────────────────────────────────────────────────────────────────────────
# 1. Centralized Tutoring Configuration (Task 4a.2)
# ─────────────────────────────────────────────────────────────────────────────

class TestCentralizedConfig:

    def test_tutoring_constants_and_single_source_of_truth(self):
        assert PROXIMITY_FEEDBACK_TOLERANCE == 1
        assert MAX_PROXIMITY_FEEDBACK_PER_STEP == 1
        assert MAX_ATTEMPTS_BEFORE_REVEAL == 3
        assert OCR_CONFIDENCE_THRESHOLD == 0.80
        assert STT_CONFIDENCE_THRESHOLD == 0.85
        assert CHILD_HELPLINE_CAMBODIA == "1280"
        assert CHILD_HELPLINE_VERIFIED_DATE == "2026-10-04"
        assert HELPLINE_SOURCE_CHECKED_DATE == "2026-10-04"
        assert HELPLINE_WRITTEN_CONFIRMATION_PENDING is True
        assert EMERGENCY_POLICE_CAMBODIA == "117"
        assert EMERGENCY_FIRE_CAMBODIA == "118"
        assert EMERGENCY_AMBULANCE_CAMBODIA == "119"
        assert "117 (Police)" in EMERGENCY_SERVICES_FALLBACK
        assert "119 (Ambulance)" in EMERGENCY_SERVICES_FALLBACK
        assert "1280 (Child Helpline 24/7)" in EMERGENCY_SERVICES_FALLBACK
        assert SAFEGUARDING_REVIEW_SLA_MINUTES == 15
        assert DEFAULT_SAFEGUARDING_OWNER == "DesignatedSchoolSafeguardingLead"
        assert SAFEGUARDING_PORTAL_URL == "https://portal.reanmore.edu.kh/safeguarding"


# ─────────────────────────────────────────────────────────────────────────────
# 2. Grader Order of Operations, Khmer Numerals & Words (Task 4a.3)
# ─────────────────────────────────────────────────────────────────────────────

class TestGraderOrderOfOperations:

    def test_khmer_numerals_normalization_and_grading(self):
        # Student answers with Khmer numerals "១៥" for expected "15"
        res = validate_socratic_answer(user_input="១៥", target_value="15")
        assert res.outcome == VALIDATION_CORRECT
        assert res.is_correct is True

        # Nested in full sentence
        res_sent = validate_socratic_answer(user_input="ខ្ញុំគិតថាគឺ ២៤", target_value="24")
        assert res_sent.is_correct is True

        # Compound vowel canonicalization: decomposed 'ត' + 'េ' + 'ា' vs precomposed 'ត' + 'ោ'
        decomposed = "ត\u17C1\u17B6"
        composed = "ត\u17C4"
        assert normalize_student_input(decomposed) == normalize_student_input(composed)

    def test_khmer_number_words(self):
        # Single digit
        res_single = validate_socratic_answer(user_input="ប្រាំ", target_value="5")
        assert res_single.is_correct is True

        # Teen compound
        res_teen = validate_socratic_answer(user_input="ដប់ប្រាំ", target_value="15")
        assert res_teen.is_correct is True

        # Tens compound
        res_twenty = validate_socratic_answer(user_input="ម្ភៃប្រាំ", target_value="25")
        assert res_twenty.is_correct is True

        # Half
        res_half = validate_socratic_answer(user_input="មួយកន្លះ", target_value="1.5")
        assert res_half.is_correct is True

    def test_locale_commas_thousands_vs_decimals(self):
        # Thousands comma: 1,000 -> 1000
        res_thous = validate_socratic_answer(user_input="1,000", target_value="1000")
        assert res_thous.is_correct is True

        # Khmer thousands: ១,០០០ -> 1000
        res_kh_thous = validate_socratic_answer(user_input="១,០០០", target_value="1000")
        assert res_kh_thous.is_correct is True

        # Decimal comma: 1,5 -> 1.5
        res_dec = validate_socratic_answer(user_input="1,5", target_value="1.5")
        assert res_dec.is_correct is True

        # Khmer decimal comma: ១,៥ -> 1.5
        res_kh_dec = validate_socratic_answer(user_input="១,៥", target_value="1.5")
        assert res_kh_dec.is_correct is True

    def test_negative_numbers(self):
        res_neg = validate_socratic_answer(user_input="-5", target_value="-5")
        assert res_neg.is_correct is True

        res_kh_neg = validate_socratic_answer(user_input="ដក ៥", target_value="-5")
        assert res_kh_neg.is_correct is True

    def test_traceability_invariant_compares_normalized_to_normalized(self):
        # Candidate 15 is verified against normalized input containing '១៥'
        raw = "ចម្លើយរបស់ខ្ញុំគឺ ១៥"
        candidates = ["15"]
        ok, valid, hallucinated = verify_number_traceability(raw, candidates)
        assert ok is True
        assert valid == ["15"]
        assert len(hallucinated) == 0

        # Hallucinated number 99 is rejected
        ok_bad, valid_bad, hal_bad = verify_number_traceability(raw, ["99"])
        assert ok_bad is False
        assert hal_bad == ["99"]


    def test_multi_turn_zero_property_confirmation_deflection(self):
        """Invariant: Zero LLM confirmation of number properties ('Is it even?', 'Is it > 10?')."""
        probe_queries = [
            "is it even?",
            "is the answer odd?",
            "is it bigger than 10?",
            "is it > 10",
            "តើជាលេខគូឬ?",
            "តើធំជាង ១០ មែនទេ?"
        ]
        for query in probe_queries:
            res = validate_socratic_answer(user_input=query, target_value="15")
            assert res.is_property_probe is True, f"Failed on probe: {query}"
            assert res.is_correct is False
            assert res.outcome == VALIDATION_PARTIAL
            assert "cannot confirm properties" in res.feedback_eng.lower() or "មិនអាចបញ្ជាក់លក្ខណៈ" in res.feedback_khmer

    def test_context_aware_locale_commas(self):
        # Expected > 1000: 4,000 -> 4000
        res_curr = validate_socratic_answer(user_input="4,000", target_value="4000")
        assert res_curr.is_correct is True

        # Currency string: 4,000 រៀល -> 4000
        res_riel = validate_socratic_answer(user_input="4,000 រៀល", target_value="4000")
        assert res_riel.is_correct is True

        # Expected decimal 1.5: 1,5 -> 1.5
        res_dec = validate_socratic_answer(user_input="1,5", target_value="1.5")
        assert res_dec.is_correct is True


# ─────────────────────────────────────────────────────────────────────────────
# 3. Identical Non-Directional Near-Miss Invariant (Task 4a.4)
# ─────────────────────────────────────────────────────────────────────────────

class TestIdenticalNearMissInvariant:

    def test_near_miss_feedback_is_identical_for_all_guesses_in_window(self):
        """Invariant: Feedback(T-1) must be strictly identical to Feedback(T+1)."""
        target = 15
        step_id = "step_add_apples"

        res_low = validate_student_answer(student_attempt="14", expected_answer=str(target), step_id=step_id)
        res_high = validate_student_answer(student_attempt="16", expected_answer=str(target), step_id=step_id)

        assert res_low.is_near_miss is True
        assert res_high.is_near_miss is True
        assert res_low.outcome == VALIDATION_PARTIAL
        assert res_high.outcome == VALIDATION_PARTIAL

        # Mathematical Invariant Check
        assert res_low.feedback_eng == res_high.feedback_eng
        assert res_low.feedback_khmer == res_high.feedback_khmer

        # Zero leakage check: Target must NOT be in the feedback
        assert str(target) not in res_low.feedback_eng
        assert str(target) not in res_low.feedback_khmer

        # Zero directional cues check: Must not leak direction (add/subtract)
        assert "add" not in res_low.feedback_eng.lower()
        assert "taking" not in res_low.feedback_eng.lower()
        assert "count on" not in res_low.feedback_eng.lower()
        assert "បូក" not in res_low.feedback_khmer
        assert "ដក" not in res_low.feedback_khmer

    def test_property_test_near_miss_invariant_across_random_targets(self):
        """Property test across 20 different numeric targets."""
        for target in range(5, 25):
            res_minus = validate_student_answer(str(target - 1), str(target))
            res_plus = validate_student_answer(str(target + 1), str(target))

            assert res_minus.is_near_miss is True
            assert res_plus.is_near_miss is True
            assert res_minus.feedback_eng == res_plus.feedback_eng
            assert str(target) not in res_minus.feedback_eng


# ─────────────────────────────────────────────────────────────────────────────
# 4. Multi-Step Praise Leak Shield (Task 4a.5)
# ─────────────────────────────────────────────────────────────────────────────

class TestMultiStepPraiseLeakShield:

    def test_praise_allows_solved_step_answer(self):
        reply = "🎉 Great job on 15! You got step 1 right!"
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=True,
            unsolved_step_values=["20", "25"],
            final_answer="25"
        )
        assert is_leak is False
        assert final_reply == reply
        assert reason == "state_allows_answer"

    def test_praise_intercepts_unsolved_future_step_leak(self):
        # Tutor praises step 1 (15) but accidentally reveals step 2 answer (20)
        leaky_reply = "🎉 Spot on with 15! Next for step 2, 15 + 5 gives 20."
        is_leak, final_reply, reason = check_tutor_response_leak(
            tutor_reply=leaky_reply,
            target_answer="15",
            is_step_solved=True,
            unsolved_step_values=["20", "25"],
            final_answer="25"
        )
        assert is_leak is True
        assert "unsolved_future_step_leak" in reason
        assert "20" not in final_reply
        assert final_reply == SAFE_PRAISE_FALLBACK_ENG

    def test_token_boundary_prevents_false_positive_on_subvalues(self):
        # Target is 15, reply mentions 150
        reply = "There are 150 centimeters in 1.5 meters."
        is_leak, final_reply, _ = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak is False
        assert final_reply == reply

    def test_digit_run_captures_adjacent_letters_and_units(self):
        # Khmer word touching digits: 'គឺ15'
        is_leak_kh, _, reason_kh = check_tutor_response_leak(
            tutor_reply="ចម្លើយគឺ15",
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_kh is True
        assert "numeric_answer_leak_detected" in reason_kh

        # Latin unit touching digits: '15cm'
        is_leak_unit, _, reason_unit = check_tutor_response_leak(
            tutor_reply="The height is 15cm",
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_unit is True
        assert "numeric_answer_leak_detected" in reason_unit

        # Word preservation: 'them' must not be corrupted to 'the'
        reply_them = "Tell them about the shapes."
        is_leak_them, final_them, _ = check_tutor_response_leak(
            tutor_reply=reply_them,
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_them is False
        assert final_them == reply_them

    def test_longest_match_khmer_number_words(self):
        # 'ដប់ប្រាំមួយ' (16) must not trigger leak on target '15' ('ដប់ប្រាំ')
        reply_16 = "ចម្លើយជំហានបន្ទាប់គឺ ដប់ប្រាំមួយ"
        is_leak_16, _, _ = check_tutor_response_leak(
            tutor_reply=reply_16,
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_16 is False

        # 'ដប់ប្រាំ' (15) correctly triggers leak on target '15'
        reply_15 = "ចម្លើយជំហានបន្ទាប់គឺ ដប់ប្រាំ"
        is_leak_15, _, reason_15 = check_tutor_response_leak(
            tutor_reply=reply_15,
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_15 is True
        assert "numeric_answer_leak_detected" in reason_15

    def test_problem_statement_numbers_exempted_unless_colliding(self):
        # Non-colliding problem number (10) is exempted when target is 15
        problem = "Sam has 10 apples and buys 5 more. How many in total?"
        reply_ok = "Remember that Sam started with 10 apples."
        is_leak, final_reply, _ = check_tutor_response_leak(
            tutor_reply=reply_ok,
            target_answer="15",
            is_step_solved=False,
            problem_text=problem
        )
        assert is_leak is False
        assert final_reply == reply_ok

        # Colliding problem number (10): If target IS 10, mentioning 10 is NOT exempted!
        reply_leaky = "The answer is 10 apples."
        is_leak_coll, _, reason_coll = check_tutor_response_leak(
            tutor_reply=reply_leaky,
            target_answer="10",
            is_step_solved=False,
            problem_text=problem
        )
        assert is_leak_coll is True
        assert "numeric_answer_leak_detected" in reason_coll

    def test_reveal_state_decoupled_from_hint_tier_3(self):
        # Hint Tier 3 alone with attempts < 3 does NOT allow answer disclosure
        reply = "The active step answer is 15."
        is_leak_h3, _, reason_h3 = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            is_reveal_state=False,
            current_hint_tier=3,
            attempts_count=1
        )
        assert is_leak_h3 is True
        assert "numeric_answer_leak_detected" in reason_h3

        # Explicit RevealState permits answer disclosure
        is_leak_rev, final_rev, reason_rev = check_tutor_response_leak(
            tutor_reply=reply,
            target_answer="15",
            is_step_solved=False,
            is_reveal_state=True
        )
        assert is_leak_rev is False
        assert reason_rev == "state_allows_answer"
        assert final_rev == reply

    def test_thousands_comma_evaluation_in_leak_checker(self):
        # 1,500 riel matches target 1500
        is_leak_thous, _, _ = check_tutor_response_leak(
            tutor_reply="The cost is 1,500 riel",
            target_answer="1500",
            is_step_solved=False
        )
        assert is_leak_thous is True

        # 1,500 matches target 1.5 (decimal comma reading)
        is_leak_dec, _, _ = check_tutor_response_leak(
            tutor_reply="It measures 1,500 meters",
            target_answer="1.5",
            is_step_solved=False
        )
        assert is_leak_dec is True

        # 1,500 does NOT leak target 15
        is_leak_15, _, _ = check_tutor_response_leak(
            tutor_reply="The cost is 1,500 riel",
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_15 is False

    def test_unspaced_comma_list_inspection(self):
        # Unspaced list "5,10,15" with target 15
        is_leak_list, _, reason = check_tutor_response_leak(
            tutor_reply="Count by fives: 5,10,15",
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_list is True
        assert "numeric_answer_leak_detected" in reason

        # List without 15
        is_leak_clean, _, _ = check_tutor_response_leak(
            tutor_reply="Count by fives: 5,10,20",
            target_answer="15",
            is_step_solved=False
        )
        assert is_leak_clean is False

    def test_arithmetic_expressions_in_leak_checker(self):
        target = "15"

        # Addition: 10 + 5
        leak, _, _ = check_tutor_response_leak("Try computing 10 + 5", target_answer=target, is_step_solved=False)
        assert leak is True

        # Unicode multiplication: 3×5
        leak_uni, _, _ = check_tutor_response_leak("Notice that 3×5 gives the amount", target_answer=target, is_step_solved=False)
        assert leak_uni is True

        # Letter multiplication: 3x5
        leak_x, _, _ = check_tutor_response_leak("Notice that 3x5 gives the amount", target_answer=target, is_step_solved=False)
        assert leak_x is True

        # Word arithmetic: half of 30
        leak_half, _, _ = check_tutor_response_leak("Think about half of 30", target_answer=target, is_step_solved=False)
        assert leak_half is True

        # Word arithmetic: thirty divided by two
        leak_div, _, _ = check_tutor_response_leak("Take thirty divided by two", target_answer=target, is_step_solved=False)
        assert leak_div is True

        # English number word: fifteen
        leak_word, _, _ = check_tutor_response_leak("The value is fifteen", target_answer=target, is_step_solved=False)
        assert leak_word is True

    def test_negative_controls_and_solved_step_preservation(self):
        # Negative control: 'making'
        leak_making, final_making, _ = check_tutor_response_leak(
            "We are making geometric shapes today.",
            target_answer="15",
            is_step_solved=False
        )
        assert leak_making is False

        # Negative control: 'them' (must not trigger 'ten' or other subwords)
        leak_them, final_them, _ = check_tutor_response_leak(
            "Ask them what they think about the problem.",
            target_answer="10",
            is_step_solved=False
        )
        assert leak_them is False

        # Negative control: Solved step's own answer in next step's question
        # Step 1 was solved (15). We are on Step 2 (target 25).
        leak_solved, final_solved, _ = check_tutor_response_leak(
            tutor_reply="Now that you found 15 in step 1, what do we add to reach the total?",
            target_answer="25",
            is_step_solved=False,
            unsolved_step_values=["25"],
            final_answer="25"
        )
        assert leak_solved is False
        assert "15 in step 1" in final_solved



# ─────────────────────────────────────────────────────────────────────────────
# 5. Categorical Tier 2 Safety Split & Counselor-First Escalation (Task 4a.6)
# ─────────────────────────────────────────────────────────────────────────────

class TestCategoricalSafetyAndEscalation:

    def setup_method(self):
        clear_safeguarding_review_queue()

    def test_tier2_child_abuse_routes_to_safeguarding_lead_never_parent(self):
        abuse_text = "my uncle comes to my room at night and hurts me"
        safety = evaluate_safety_tier(abuse_text)
        assert safety.is_safe is False
        assert safety.severity_tier == 2
        assert safety.tier == "TIER2_CHILD_ABUSE"

        decision = dispatch_escalation_alert(safety, student_token="STU-9901")
        assert decision["escalated"] is True
        assert decision["target_recipient"] == "SCHOOL_SAFEGUARDING_LEAD"
        assert "parent" not in decision["target_recipient"].lower()
        assert decision["student_token"] == "STU-9901"
        assert decision["tutor_state"] == "PAUSED"

        # Check isolated payload: No raw text
        payload = decision["payload"]
        assert "student_token" in payload
        assert "hurts me" not in payload.values()

        # Check queue record
        q = get_safeguarding_review_queue()
        assert len(q) == 1
        assert q[0].student_token == "STU-9901"
        assert q[0].owner == DEFAULT_SAFEGUARDING_OWNER
        assert q[0].sla_minutes == 15

    def test_content_free_notification_ping(self):
        abuse_text = "someone is beating me at home"
        safety = evaluate_safety_tier(abuse_text)
        decision = dispatch_escalation_alert(safety, student_token="STU-PING-01")

        ping = decision["notification_ping"]
        assert "STU-PING-01" in ping
        assert "SLA: 15m" in ping
        assert SAFEGUARDING_PORTAL_URL in ping
        assert "beating" not in ping
        assert "home" not in ping

    def test_recusal_conflict_routes_to_district_focal_point(self):
        abuse_text = "the school teacher is hurting me"
        safety = evaluate_safety_tier(abuse_text)
        decision = dispatch_safety_alert(
            session_id="sess_recusal",
            severity_tier=2,
            category="CHILD_ABUSE",
            text_snippet="teacher hurting me",
            has_recusal_conflict=True
        )
        assert decision["target_recipient"] == "DISTRICT_SAFEGUARDING_FOCAL_POINT"
        assert decision["action"] == "DISPATCH_DISTRICT_RECUSAL_ALERT"
        q = get_safeguarding_review_queue()
        assert q[-1].escalation_level == 3

    def test_sla_auto_escalation_after_15_minutes(self):
        from datetime import datetime, timezone, timedelta
        abuse_text = "i am being hurt"
        safety = evaluate_safety_tier(abuse_text)
        decision = dispatch_escalation_alert(safety, student_token="STU-SLA-01")

        q = get_safeguarding_review_queue()
        assert len(q) == 1
        assert q[0].escalation_level == 1

        # Simulate 16 minutes later
        now = datetime.now(timezone.utc)
        simulated_future = now + timedelta(minutes=16)
        escalated = check_and_escalate_unacknowledged(current_time_utc=simulated_future)

        assert len(escalated) == 1
        assert escalated[0].escalation_level == 2
        assert escalated[0].target_recipient == "SCHOOL_PRINCIPAL_BACKUP"
        assert escalated[0].status == "AUTO_ESCALATED"

    def test_acknowledgment_flow(self):
        harm_text = "i want to hurt myself"
        safety = evaluate_safety_tier(harm_text)
        decision = dispatch_escalation_alert(safety, student_token="STU-ACK-01")
        event_id = decision["event_id"]

        success = acknowledge_safeguarding_alert(event_id, acknowledged_by="Counselor_Sophea")
        assert success is True

        q = get_safeguarding_review_queue()
        assert q[0].status == "ACKNOWLEDGED"
        assert q[0].acknowledged_by == "Counselor_Sophea"
        assert q[0].acknowledged_at_utc is not None

    def test_tier2_self_harm_routes_to_counselor_and_provides_1280_helpline(self):
        harm_text = "i want to die i am cutting myself"
        safety = evaluate_safety_tier(harm_text)
        assert safety.is_safe is False
        assert safety.severity_tier == 2
        assert safety.tier == "TIER2_SELF_HARM"

        decision = dispatch_escalation_alert(safety, student_token="STU-HARM-01")
        assert decision["escalated"] is True
        assert decision["target_recipient"] == "SCHOOL_COUNSELOR"
        assert CHILD_HELPLINE_CAMBODIA in decision["child_facing_guidance"]
        assert decision["tutor_state"] == "PAUSED"

    def test_tier2_immediate_danger_routes_to_coordinator(self):
        danger_text = "a stranger with a knife is following me near school"
        safety = evaluate_safety_tier(danger_text)
        assert safety.is_safe is False
        assert safety.tier == "TIER2_IMMEDIATE_DANGER"

        decision = dispatch_escalation_alert(safety, student_token="STU-DANGER-01")
        assert decision["escalated"] is True
        assert decision["target_recipient"] == "SCHOOL_SAFETY_COORDINATOR"
        assert "trusted adult" in decision["child_facing_guidance"]

