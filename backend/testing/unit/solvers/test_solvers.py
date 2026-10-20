"""
File: testing/test_solvers.py
Description: Comprehensive Unit and Integration Tests for Math and Science Solvers & Answer Validators.
"""

import os
import sys
from fastapi.testclient import TestClient

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

from services.math_service.app.main import app as math_app
from services.math_service.app.validator import verify_equivalence as math_verify, parse_numeric_or_fraction
from services.math_service.app.solvers.algebra import solve_math
from services.science_service.app.main import app as science_app
from services.science_service.app.validator import verify_science_concept
from services.science_service.app.solvers.physics import solve_physics
from services.science_service.app.solvers.chemistry import solve_chemistry
from services.science_service.app.solvers.biology import solve_biology

math_client = TestClient(math_app)
science_client = TestClient(science_app)


# =========================================================================
# 1. Math Validator & Equivalence Tests
# =========================================================================

def test_math_numeric_exact_and_units():
    assert math_verify("5", "5") is True
    assert math_verify("5 cookies", "5") is True
    assert math_verify("12 cm", "12") is True
    assert math_verify("3.5 kg", "3.5") is True
    assert math_verify("about 10 apples", "10") is True


def test_math_word_numbers():
    assert math_verify("five", "5") is True
    assert math_verify("zero", "0") is True
    assert math_verify("ten", "10") is True
    assert math_verify("seven", "7") is True
    assert math_verify("twelve", "12") is True


def test_math_fractions_and_decimals():
    assert math_verify("1/2", "0.5") is True
    assert math_verify("0.5", "1/2") is True
    assert math_verify("half", "1/2") is True
    assert math_verify("2/4", "1/2") is True
    assert math_verify("3/4", "0.75") is True
    assert math_verify("quarter", "0.25") is True
    assert math_verify("one third", "0.333") is True


def test_math_sympy_algebraic_equivalence():
    assert math_verify("3*x = 9", "x = 3") is True
    assert math_verify("x + 2 = 5", "x = 3") is True
    assert math_verify("2*x = 6", "x = 3") is True


def test_math_mismatches():
    assert math_verify("5", "6") is False
    assert math_verify("1/2", "3/4") is False
    assert math_verify("x = 4", "x = 3") is False


# =========================================================================
# 2. Math Solver & FastAPI Endpoints
# =========================================================================

def test_math_solver_arithmetic():
    res = solve_math("25 + 17")
    assert res["success"] is True
    assert res["solution"] == "42"
    assert len(res["steps"]) >= 2


def test_math_solver_subtraction_and_division():
    res_sub = solve_math("50 - 15")
    assert res_sub["success"] is True
    assert res_sub["solution"] == "35"

    res_div = solve_math("48 / 6")
    assert res_div["success"] is True
    assert res_div["solution"] == "8"


def test_math_service_solve_endpoint():
    res = math_client.post("/solve", json={"query": "12 * 4"})
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["solution"] == "48"


def test_math_service_validate_endpoint():
    res = math_client.post("/validate", json={"student_attempt": "5 cookies", "expected_step": "5"})
    assert res.status_code == 200
    assert res.json()["equivalent"] is True


# =========================================================================
# 3. Science Conceptual Validator Tests
# =========================================================================

def test_science_synonyms_evaporation_condensation():
    assert verify_science_concept("it evaporates into steam", "evaporation") is True
    assert verify_science_concept("liquid turns into gas", "evaporation") is True
    assert verify_science_concept("water vapor", "evaporation") is True
    assert verify_science_concept("gas to liquid", "condensation") is True
    assert verify_science_concept("water droplets form", "condensation") is True


def test_science_synonyms_biology_and_physics():
    assert verify_science_concept("powerhouse of the cell", "mitochondria") is True
    assert verify_science_concept("plants make food using sunlight", "photosynthesis") is True
    assert verify_science_concept("gravity pulls it down", "gravity") is True
    assert verify_science_concept("opposes motion", "friction") is True


def test_science_token_overlap_matching():
    assert verify_science_concept("light energy converted to chemical energy", "photosynthesis light energy") is True


# =========================================================================
# 4. Science Solvers & FastAPI Endpoints
# =========================================================================

def test_physics_solver_mechanics():
    res = solve_physics("mass: 5 kg, acceleration: 2 m/s^2")
    assert res["success"] is True
    assert "10.0 N" in res["solution"]
    assert len(res["steps"]) >= 3


def test_chemistry_solver_states_and_mass():
    res = solve_chemistry("what happens when water boils?")
    assert res["success"] is True
    assert "Evaporation" in res["solution"]

    mass_res = solve_chemistry("molar mass of H2O")
    assert mass_res["success"] is True
    assert "18.02" in mass_res["solution"] or "18.01" in mass_res["solution"]


def test_biology_solver_photosynthesis():
    res = solve_biology("How do plants perform photosynthesis?")
    assert res["success"] is True
    assert "Glucose" in res["solution"]
    assert len(res["steps"]) >= 3


def test_science_service_solve_and_validate_endpoints():
    res_solve = science_client.post("/solve", json={"query": "Explain photosynthesis in plants"})
    assert res_solve.status_code == 200
    assert res_solve.json()["success"] is True

    res_val = science_client.post("/validate", json={"student_attempt": "it evaporates", "expected_step": "evaporation"})
    assert res_val.status_code == 200
    assert res_val.json()["equivalent"] is True


def test_science_false_positive_prevention():
    assert verify_science_concept("is", "photosynthesis") is False
    assert verify_science_concept("to", "photosynthesis") is False
    assert verify_science_concept("in", "condensation") is False
    assert verify_science_concept("no", "photosynthesis") is False
    assert verify_science_concept("a", "evaporation") is False


def test_math_punctuation_and_double_equals():
    from services.math_service.app.validator import validate_expression
    assert validate_expression("What is 5 + 5?") is True
    assert validate_expression("Lily's 10 apples") is True
    assert math_verify("x == 3", "x = 3") is True


def test_math_offline_degraded_when_gemini_unset(monkeypatch):
    import services.math_service.app.solvers.algebra as alg
    monkeypatch.setattr(alg, "GEMINI_API_KEY", "")
    mul_res = alg.solve_math("3 boxes with 4 cookies each")
    assert mul_res["success"] is False
    assert mul_res["solution"] is None
    assert mul_res["steps"] == []
    assert "unavailable" in mul_res["error"].lower()


def test_science_offline_degraded_when_gemini_unset(monkeypatch):
    import services.science_service.app.solvers.biology as bio
    import services.science_service.app.solvers.chemistry as chem
    import services.science_service.app.solvers.physics as phys

    monkeypatch.setattr(bio, "GEMINI_API_KEY", "")
    monkeypatch.setattr(chem, "GEMINI_API_KEY", "")
    monkeypatch.setattr(phys, "GEMINI_API_KEY", "")

    bio_res = bio.solve_biology_ai("unknown cellular enzyme kinetics")
    assert bio_res["success"] is False
    assert bio_res["solution"] is None
    assert bio_res["steps"] == []
    assert "unavailable" in bio_res["error"].lower()

    chem_res = chem.solve_chemistry_ai("complex precipitation reaction between barium and sulfate")
    assert chem_res["success"] is False
    assert chem_res["solution"] is None
    assert chem_res["steps"] == []
    assert "unavailable" in chem_res["error"].lower()

    phys_res = phys.solve_physics_ai("calculate angular momentum of spinning top")
    assert phys_res["success"] is False
    assert phys_res["solution"] is None
    assert phys_res["steps"] == []
    assert "unavailable" in phys_res["error"].lower()


def test_biology_mitochondria_falls_through_grade_1_3_rules(monkeypatch):
    import services.science_service.app.solvers.biology as bio
    # 1. Deterministic Grade 1-3 matcher does NOT match mitochondria anymore
    rule_res = bio.solve_grade_1_3_biology("What is mitochondria in a cell?")
    assert rule_res["success"] is False

    # 2. Main solve_biology falls through to AI/Qdrant path (degraded if unconfigured)
    monkeypatch.setattr(bio, "GEMINI_API_KEY", "")
    full_res = bio.solve_biology("What is mitochondria in a cell?")
    assert full_res["success"] is False
    assert full_res["solution"] is None
    assert "GEMINI_API_KEY" in full_res.get("error", "")
