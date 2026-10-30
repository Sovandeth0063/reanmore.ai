"""
File: services/chemistry_service/app/main.py
Description: Chemistry Solver Service API. Exposes POST /solve endpoint routing to 
             either the equation balancer or molar mass calculator.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List

from app.engine.balancer import balance_reaction
from app.engine.molar_mass import calculate_molar_mass

app = FastAPI(title="Science Chatbot - Chemistry Service")

class SolveRequest(BaseModel):
    query: str = Field(..., description="The chemistry query to solve (balancing or molar mass)")
    context: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Optional extra context")

class SolveResponse(BaseModel):
    solution: Optional[str] = None
    steps: List[str] = Field(default_factory=list)
    success: bool
    error: Optional[str] = None

@app.post("/solve", response_model=SolveResponse)
def solve(request: SolveRequest):
    query_str = request.query.strip()
    
    # Identify whether the query targets balancing an equation or calculating molar mass
    is_balance = (
        any(keyword in query_str.lower() for keyword in ["balance", "reaction", "equation"]) or 
        "->" in query_str or 
        "=" in query_str
    )
    
    if is_balance:
        result = balance_reaction(query_str)
    else:
        result = calculate_molar_mass(query_str)
        
    return SolveResponse(**result)

@app.get("/health")
def health():
    return {"status": "healthy"}
