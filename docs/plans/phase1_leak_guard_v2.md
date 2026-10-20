# Phase 1C Implementation Plan: Leak Guard v2 & Pedagogical Invariants

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/ReanMore_Architecture_v2.1.md) (Section 10.1, Appendix H)  
> **Status:** COMPLETED & VERIFIED ✅  
> **Prerequisites:** Phase 1A & Phase 1B complete.

---

## 1. Objectives & Scope

Phase 1C upgrades `backend/orchestrator/app/services/guardrails/leak_guard.py` to **Leak Guard v2**, eliminating false-positive over-blocking while maintaining a statistical 0-leak defense across text and visual payloads:
1. **Given Operands Allowlist:** Guarantee that numbers given in the student's problem (e.g. 15 and 27 in "15 + 27") are never falsely blocked.
2. **Context-Scoped Target Verification:** Differentiate between target answers in student-facing prompts and distinct numbers inside parallel examples.
3. **Structural Example Validation:** Permit terms like "equals" inside verified parallel examples without triggering disclosure flags.
4. **Narrowed 6-Token Disclosure Window:** Flag disclosure phrases ("the answer is") only when followed within 6 tokens by a numeric quantity.
5. **VisualSpec JSON Security Scanning:** Inspect all labels, alt-text, and numerical parameters in visual models.
6. **Adversarial Test Suite:** Expand adversarial test coverage to 100 benchmark cases.

---

## 2. Current State vs Target Architecture

| Component | Current Implementation (Leak Guard v1) | Target Specification (Leak Guard v2) | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| **Problem Operands** | Blocked if problem numbers collide with active/unsolved targets | Explicitly allowlisted operands from student problem text | `CONFLICTS` | [`leak_guard.py:L305-330`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/guardrails/leak_guard.py#L305-L330) |
| **Disclosure Phrasing** | Broad regex matching on "equals" / "gives you" anywhere in text | Narrowed 6-token distance window before digit or number-word | `CONFLICTS` | [`leak_guard.py:L78-82`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/guardrails/leak_guard.py#L78-L82) |
| **Parallel Examples** | Can trigger false leak if example uses standard math syntax | Structural validation of `helpful_example` block | `MISSING` | Target: `leak_guard.py:validate_structural_example` |
| **Visual Model Leak** | Not scanned | Multi-point parameter, label, and alt-text inspection | `MISSING` | Target: `leak_guard.py:scan_visual_spec` |
| **Telemetry Logging** | Logs to stdout / file logger only | Logs `LEAK_BLOCKED` event directly to `gap_events` table | `PARTIAL` | [`leak_guard.py:L35-36`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/services/guardrails/leak_guard.py#L35-L36) |

---

## 3. Step-by-Step Implementation Steps

### Step 1C.1: Given Operands Allowlist

Refactor the token extraction logic in `leak_guard.py`:
- Extract all literal numbers present in the student's problem statement.
- Add these numbers to `allowed_operand_tokens`.
- In tutor prose, if a token matches `allowed_operand_tokens`, it is permitted as valid pedagogical restatement of the question:
  ```python
  # Example: "In 15 + 27, let's look at 15 first" -> 15 is permitted even if Step 1 target was 15!
  if token in allowed_operand_tokens and not is_disclosure_phrase_near(text, token):
      continue
  ```

### Step 1C.2: 6-Token Narrowed Disclosure Window

Replace the unconstrained phrase matching regex with a token-distance scanner:
```python
DISCLOSURE_PREFIXES = [
    r"the\s+answer\s+is",
    r"correct\s+answer\s+is",
    r"so\s+it'?s",
    r"equals",
    r"is\s+equal\s+to",
    r"gives\s+you",
    r"therefore\s+we\s+get"
]

def check_disclosure_window(text: str, target_val: Fraction) -> bool:
    tokens = text.split()
    for i, token in enumerate(tokens):
        if matches_disclosure_prefix(token):
            window = tokens[i+1 : i+7]  # 6-token lookahead
            for w_tok in window:
                if evaluates_to_target(w_tok, target_val):
                    return True  # LEAK: "The answer is [within 6 tokens] 42"
    return False
```

### Step 1C.3: Structural Example Validation

In Socratic 4-Part Step Cards, the `helpful_example` field contains an isomorphic worked problem (e.g. $7 + 5$ for an $8 + 6$ problem):
- Verify that none of the numbers in the example equal the student's problem operands or active/unsolved targets.
- Once verified, exempt the `helpful_example` block from raw disclosure phrase flagging (e.g. "$7 + 3 = 10$" is valid pedagogical guidance in an example).

### Step 1C.4: VisualSpec Security Scanner

Create `scan_visual_spec(spec: VisualSpec, target_values: Set[Fraction]) -> bool`:
- Traverse all fields in `spec.params`.
- Ensure no parameter scalar equals any active or future step target when `mode != "reveal"`.
- Run `labels` and `alt_text` through `check_tutor_response_leak`.
- If a leak is found, quarantine the visual spec and log `LEAK_BLOCKED` to `gap_events`.

### Step 1C.5: Adversarial Golden Suite Expansion

Expand `backend/testing/unit/socratic/test_leak_guard_stage.py` to 100 test cases covering:
- English number words ("fourteen", "twenty-five", "three quarters").
- Arithmetic combinations ("10 + 4", "2 x 7", "28 / 2").
- Homoglyphs and spaced digits ("1 4", "1-4").
- Edge-case proximity prompts ("You are 1 away!", "So close!").
- Visual model parameters and labels.

---

## 4. Verification & Testing Protocol

Execute from `backend/`:

```powershell
# Run the complete Leak Guard v2 test suite (including 100 adversarial cases)
& ..\.venv\Scripts\python.exe -m pytest testing/unit/socratic/test_leak_guard_stage.py -v
```

### Exit Criteria
- [ ] 0 leaks detected across all 100 adversarial benchmark test cases.
- [ ] Problem operands (e.g. "15" and "27") are not falsely quarantined.
- [ ] Terms like "equals" inside verified parallel examples pass cleanly.
- [ ] Any actual disclosure within 6 tokens is caught and quarantined with structured pedagogical fallback.
