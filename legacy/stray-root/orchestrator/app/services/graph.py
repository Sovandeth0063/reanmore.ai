"""
File: orchestrator/app/services/graph.py
Description: Defines the compiled LangGraph StateGraph representing the Socratic tutoring loop workflow,
             incorporating subject classification, correctness evaluation, and adaptive hinting.
"""

from langgraph.graph import StateGraph, START, END
# pyrefly: ignore [missing-import]
from langgraph.checkpoint.redis import RedisSaver
from app.services.session import session_manager
from app.core.logging import logger

from app.services.state import SocraticTutorState
from app.services.nodes.router import classify_subject_node
from app.services.nodes.tutor_loop import tutor_loop_node
from app.services.nodes.hint_generator import generate_hint_node
from app.services.nodes.practice_generator import generate_practice_node

def route_next_node(state: SocraticTutorState) -> str:
    """
    Conditional edge router that directs the tutoring flow:
    - Route to practice_generator if the user wants another practice question.
    - Route to hint_generator if the student made a mistake or subject is GENERAL.
    - Otherwise, end the step execution and return feedback.
    """
    feedback = state.get("tutor_feedback", "")
    student_attempt = state.get("student_attempt", "").strip().lower()
    subject = state.get("subject", "GENERAL")
    
    # 1. User wants a practice problem
    if any(keyword in student_attempt for keyword in ["practice", "another example", "give me another", "practice problem"]):
        return "generate_practice"
        
    # 2. Tutor loop detected incorrect answer or is GENERAL query (needs LLM generation)
    if feedback == "__TRIGGER_HINT__" or subject == "GENERAL":
        return "generate_hint"
        
    # 3. Else, return response to client (end step processing)
    return END

# Construct LangGraph Socratic Tutor Workflow
builder = StateGraph(SocraticTutorState)

# Add Nodes
builder.add_node("classify_subject", classify_subject_node)
builder.add_node("tutor_loop", tutor_loop_node)
builder.add_node("generate_hint", generate_hint_node)
builder.add_node("generate_practice", generate_practice_node)

# Connect Nodes (Edges)
builder.add_edge(START, "classify_subject")
builder.add_edge("classify_subject", "tutor_loop")

# Add Routing Logic from Tutor Loop
builder.add_conditional_edges(
    "tutor_loop",
    route_next_node,
    {
        "generate_hint": "generate_hint",
        "generate_practice": "generate_practice",
        END: END
    }
)

# Terminate workflow after generating hint
builder.add_edge("generate_hint", END)

# Practice Generator loops back to Tutor Loop to solve the new exercise
builder.add_edge("generate_practice", "tutor_loop")

# Compile with Redis checkpoint saver
checkpointer = RedisSaver(redis_client=session_manager.redis_client)
try:
    checkpointer.setup()
except Exception as e:
    logger.error(f"Failed to setup RedisSaver checkpointer: {e}")

socratic_graph = builder.compile(checkpointer=checkpointer)
