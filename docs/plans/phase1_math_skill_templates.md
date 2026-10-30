# Phase 1A Implementation Plan: In-Process Math Engine & Skill Templates

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](../../docs/ReanMore_Architecture_v2.1.md) (Sections 5.2, 7.1, 7.2, 8, Appendix C)  
> **Status:** COMPLETED & VERIFIED ✅  
> **Prerequisites:** Phase 0 complete; `sympy` available in Python environment.

---

## 1. Objectives & Scope

Phase 1A eliminates the separate math microservice and Google Gemini dependency by establishing an **in-process SymPy CAS engine** and a deterministic **Skill Template Library** directly inside the orchestrator:
1. **In-Process Math Engine:** Migrate SymPy AST and exact evaluation into `backend/orchestrator/app/services/socratic/math_engine/`.
2. **Implement 6 MVP Skill Templates:** Pure deterministic decomposition, parallel isomorphic examples, and progressive hints for Grades 1-6.
3. **Word Problem Parse Verification Pipeline:** 7-stage verification (operand existence, number coverage, operator sanity) plus free child confirmation prompt.
4. **Unmatched Problem Handling:** Safe fallback emitting `NO_SKILL_MATCH` gap event and honest notice with zero quota penalty.

---

## 2. Current State vs Target Architecture

| Component | Current Implementation | Target Specification | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| **Solver Architecture** | Separate HTTP microservice (:9001) | In-process Python module inside orchestrator | `CONFLICTS` | [`docker-compose.yml:L84-95`](../../backend/docker-compose.yml#L84-L95) |
| **Word Problem Solver** | Google Gemini cloud API call (`google.generativeai`) | In-process SymPy CAS + Parse Verifier + Skill Templates | `CONFLICTS` | [`algebra.py:L12-21`](../../backend/services/math_service/app/solvers/algebra.py#L12-L21) |
| **Decomposition Logic** | Generic 2-step ("Identify Numbers" -> "Calculate") | Pedagogical milestones (Make a ten, Trade 10 ones, etc.) | `CONFLICTS` | [`algebra.py:L93-100`](../../backend/services/math_service/app/solvers/algebra.py#L93-L100) |
| **Parallel Example** | Often re-uses problem numbers or relies on LLM | `make_distinct_example()` with strictly non-overlapping numbers | `MISSING` | Target: `skills/base.py` |
| **Parse Verification** | Basic regex matching on digits | 7-stage parse verifier with child confirmation prompt | `MISSING` | Target: `parse_verifier.py` |

---

## 3. Step-by-Step Implementation Steps

### Step 1A.1: In-Process CAS Engine (`backend/orchestrator/app/services/socratic/math_engine/`)

Create `cas.py` and `evaluator.py`:
- Use `sympy.sympify` and `sympy.simplify` for symbolic equivalence checking.
- Exact arithmetic validation (fractions, decimals, negative integers, units).
- Zero external HTTP calls or cloud API dependencies.

```python
# cas.py contract
def evaluate_exact(expr: str) -> Fraction: ...
def is_mathematically_equivalent(student_expr: str, target_expr: str) -> bool: ...
```

### Step 1A.2: Skill Template Protocol & Registry (`backend/orchestrator/app/services/socratic/skills/`)

Implement the formal `Skill` protocol and registry:
```python
class StepTemplate(BaseModel):
    step_number: int
    title: str
    mission: str
    clue: str
    helpful_example: str
    your_turn: str
    expected_answer: str
    concept: str
    visual_spec: Dict[str, Any]

class Skill(Protocol):
    skill_id: str
    grade_band: str
    def matches(self, problem: Dict[str, Any]) -> bool: ...
    def build_steps(self, problem: Dict[str, Any]) -> List[StepTemplate]: ...
    def make_distinct_example(self, problem: Dict[str, Any]) -> Dict[str, Any]: ...
```

### Step 1A.3: Implement the 6 Core Math Skills

Create dedicated modules under `skills/`:
1. `add_within_20.py`:
   - Decomposition: Step 1: Make a ten ($8 + 6 = 8 + 2 + 4$); Step 2: Add remaining ones ($10 + 4 = 14$).
   - Visual: `ten_frame`.
2. `sub_within_20.py`:
   - Decomposition: Step 1: Count back to 10 ($14 - 6 = 14 - 4 - 2$); Step 2: Subtract remaining ($10 - 2 = 8$).
   - Visual: `number_line`.
3. `add_2digit_regroup.py`:
   - Decomposition: Step 1: Add ones; Step 2: Trade 10 ones for 1 ten; Step 3: Add tens column.
   - Visual: `base_ten_blocks`.
4. `sub_2digit_borrow.py`:
   - Decomposition: Step 1: Check ones; Step 2: Regroup 1 ten into 10 ones; Step 3: Subtract ones & tens.
   - Visual: `base_ten_blocks`.
5. `mult_tables.py`:
   - Decomposition: Step 1: Identify groups and items; Step 2: Repeated addition / skip count.
   - Visual: `array_grid`.
6. `fraction_equivalent.py`:
   - Decomposition: Step 1: Identify denominator split; Step 2: Scale numerator.
   - Visual: `fraction_bar`.
7. `one_step_word_problem.py`:
   - Decomposition: Step 1: Map part-whole relationship; Step 2: Solve single arithmetic operation.
   - Visual: `bar_model`.

### Step 1A.4: Word Problem Parse Verification Pipeline (`parse_verifier.py`)

Implement the 7-stage verification pipeline:
1. **Extract Quantities:** Extract all numeric tokens from the text (e.g. "Dara has 15 marbles, gives 7 to Bopha").
2. **Operand Coverage:** Ensure all extracted quantities map to the arithmetic formula ($15 - 7$).
3. **Operator Sanity Check:** Verify whether keyword cues ("gives away", "in all", "each") match the chosen operation.
4. **Token-to-Number Ratio:** Deflect overly long essays or confusing narrative spam.
5. **Grade-Band Suitability Check:** Flag numbers exceeding Grade 1-6 standards (e.g. $10^{12}$).
6. **Single Unknown Check:** Ensure there is exactly one unknown quantity to solve.
7. **Child Confirmation Prompt:**
   - If confidence is $< 0.90$ but plausible: prompt the student: *"Did you mean: Dara started with 15 and gave 7 away? (15 - 7 = ?) [Yes] [No]"*.
   - Free turn: confirmation clicks do not consume daily problem quota.

---

## 4. Verification & Testing Protocol

Execute from `backend/`:

```powershell
# 1. Test in-process CAS equivalence
& ..\.venv\Scripts\python.exe -m pytest testing/unit/solvers/test_cas_engine.py -v

# 2. Test 6 skill templates (decomposition, isomorphic example generation)
& ..\.venv\Scripts\python.exe -m pytest testing/unit/socratic/test_skill_templates.py -v

# 3. Test word problem parse verifier & child confirmation
& ..\.venv\Scripts\python.exe -m pytest testing/unit/socratic/test_parse_verifier.py -v
```

### Exit Criteria
- [ ] In-process CAS runs 100% offline without network requests or external microservice calls.
- [ ] All skill templates generate the appropriate number of milestone cards (1 for direct facts within 10, 2-4 for strategy-driven problems) and answer-safe visual specs.
- [ ] `make_distinct_example()` produces numbers with zero overlap with the student's problem.
- [ ] Parse verifier flags mismatched numbers and triggers child confirmation without deducting quota.
