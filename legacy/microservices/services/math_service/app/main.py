"""
File: services/math_service/app/main.py
Description: FastAPI microservice exposing POST /solve and POST /validate endpoints 
             for compiling steps and verifying mathematical statement equivalence.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

try:
    from app.validator import validate_expression, verify_equivalence
    from app.solvers.algebra import solve_math
except ImportError:
    from services.math_service.app.validator import validate_expression, verify_equivalence
    from services.math_service.app.solvers.algebra import solve_math

app = FastAPI(title="Science Chatbot - Math Service")


class SolveRequest(BaseModel):
    query: str = Field(..., description="The mathematical expression/equation to solve")
    subject: Optional[str] = Field("MATH", description="Subject domain")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional extra context")


class SolveResponse(BaseModel):
    solution: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    structured_steps: Optional[List[Dict[str, Any]]] = None
    success: bool
    error: Optional[str] = None


class ValidateRequest(BaseModel):
    student_attempt: str = Field(..., description="The student's proposed math step")
    expected_step: str = Field(..., description="The expected math step equation or answer")
    subject: Optional[str] = Field("MATH", description="Subject domain")


class ValidateResponse(BaseModel):
    equivalent: bool
    error: Optional[str] = None


@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    if not validate_expression(request.query):
        return SolveResponse(
            success=False,
            error="Query contains disallowed characters. Only standard mathematical characters are supported."
        )
    
    result = solve_math(request.query, request.context)
    return SolveResponse(**result)


@app.post("/validate", response_model=ValidateResponse)
def validate(request: ValidateRequest):
    if not validate_expression(request.student_attempt):
        return ValidateResponse(equivalent=False, error="Attempt contains disallowed characters.")
    
    equivalent = verify_equivalence(request.student_attempt, request.expected_step)
    return ValidateResponse(equivalent=equivalent)


@app.get("/health")
def health():
    return {"status": "healthy", "service": "math_service"}
