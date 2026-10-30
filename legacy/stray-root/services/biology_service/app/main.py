"""
File: services/biology_service/app/main.py
Description: Biology Solver Service API. Exposes POST /solve endpoint routing to 
             the genetics transcription/translation solver engine.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from app.solvers.genetics import solve_biology

app = FastAPI(title="Science Chatbot - Biology Service")

class SolveRequest(BaseModel):
    query: str = Field(..., description="The biology query to solve")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional extra context")

class SolveResponse(BaseModel):
    solution: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None

@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    result = solve_biology(request.query, request.context)
    return SolveResponse(**result)

@app.get("/health")
def health():
    return {"status": "healthy"}
