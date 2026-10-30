"""
File: services/physics_service/app/main.py
Description: Physics Solver Service API. Exposes POST /solve endpoint routing to 
             the mechanics solver engine.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from app.solvers.mechanics import solve_physics

app = FastAPI(title="Science Chatbot - Physics Service")

class SolveRequest(BaseModel):
    query: str = Field(..., description="The physics query to solve")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional extra context")

class SolveResponse(BaseModel):
    solution: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None

@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    result = solve_physics(request.query, request.context)
    return SolveResponse(**result)

@app.get("/health")
def health():
    return {"status": "healthy"}
