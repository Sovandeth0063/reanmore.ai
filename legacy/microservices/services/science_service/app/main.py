"""
File: services/science_service/app/main.py
Description: Unified Science Service API exposing POST /solve, POST /validate, and /health.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

try:
    from app.validator import verify_science_concept
    from app.solvers.physics import solve_physics
    from app.solvers.chemistry import solve_chemistry
    from app.solvers.biology import solve_biology
except ImportError:
    from services.science_service.app.validator import verify_science_concept
    from services.science_service.app.solvers.physics import solve_physics
    from services.science_service.app.solvers.chemistry import solve_chemistry
    from services.science_service.app.solvers.biology import solve_biology

app = FastAPI(
    title="Science Chatbot - Unified Science Service",
    description="Unified solver service for elementary & middle school physics, chemistry, and biology."
)


class SolveRequest(BaseModel):
    query: str = Field(..., description="The science query to solve")
    subject: Optional[str] = Field("SCIENCE", description="Optional subject override: PHYSICS, CHEMISTRY, or BIOLOGY")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Grade level and additional context")


class SolveResponse(BaseModel):
    solution: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None


class ValidateRequest(BaseModel):
    student_attempt: str = Field(..., description="The student's submitted step or answer")
    expected_step: str = Field(..., description="The target step answer or concept")
    subject: Optional[str] = Field("SCIENCE", description="Subject domain for validation")


class ValidateResponse(BaseModel):
    equivalent: bool
    error: Optional[str] = None


@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    query = request.query.strip()
    subject = (request.subject or "").upper()
    context = request.context or {}

    # If subject explicitly specified, route directly
    if subject == "PHYSICS":
        result = solve_physics(query, context)
        return SolveResponse(**result)
    elif subject == "CHEMISTRY":
        result = solve_chemistry(query, context)
        return SolveResponse(**result)
    elif subject == "BIOLOGY":
        result = solve_biology(query, context)
        return SolveResponse(**result)

    # Automatic topic detection based on keywords
    query_lower = query.lower()

    if any(w in query_lower for w in ["dna", "rna", "plant", "animal", "cell", "mitosis", "organism", "photosynthesis", "codon", "mitochondria"]):
        result = solve_biology(query, context)
        if result.get("success"):
            return SolveResponse(**result)

    if any(w in query_lower for w in ["water", "liquid", "gas", "solid", "ice", "steam", "boil", "melt", "freeze", "molar mass", "reaction", "element", "molecule", "atom"]):
        result = solve_chemistry(query, context)
        if result.get("success"):
            return SolveResponse(**result)

    if any(w in query_lower for w in ["force", "gravity", "speed", "velocity", "acceleration", "friction", "motion", "mass", "circuit"]):
        result = solve_physics(query, context)
        if result.get("success"):
            return SolveResponse(**result)

    # Default to physics / general science
    result = solve_physics(query, context)
    return SolveResponse(**result)


@app.post("/validate", response_model=ValidateResponse)
def validate(request: ValidateRequest):
    is_equivalent = verify_science_concept(request.student_attempt, request.expected_step)
    return ValidateResponse(equivalent=is_equivalent)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "science_service"}
