"""
File: orchestrator/app/services/nodes/router.py
Description: LangGraph router node that executes the multi-layered NLU Pipeline
             to classify intent, normalize equations, resolve pronouns, and extract keywords.
"""

from app.core.logging import logger
from app.services.state import SocraticTutorState
from app.services.nodes.nlu_pipeline import nlu_pipeline

async def classify_subject_node(state: SocraticTutorState) -> dict:
    """
    LangGraph node to execute the NLU pipeline and classify query subject/intent.
    """
    query = state.get("query", "").strip()
    history = state.get("history", []) or []
    
    if not query:
        return {
            "subject": "GENERAL",
            "user_intent": "CHITCHAT",
            "resolved_query": "",
            "search_keywords": ""
        }

    try:
        # Execute the 5-Layered NLU Pipeline
        language = state.get("language", "en")
        nlu_results = nlu_pipeline.execute_pipeline(query, history, language)
        
        # Subject stickiness: keep previous subject if they are doing step attempts, 
        # practices, or asking follow-ups, unless they are initiating a new solving process.
        existing_subject = state.get("subject")
        final_subject = nlu_results["subject"]
        if existing_subject and nlu_results["user_intent"] != "INITIAL_SOLVE":
            final_subject = existing_subject
            logger.info(f"Router Node: Keeping sticky subject '{final_subject}' for turn.")

        logger.info(
            f"Router Node Results:\n"
            f"  Intent: {nlu_results['user_intent']}\n"
            f"  Subject: {final_subject}\n"
            f"  Normalized: {nlu_results['query']}\n"
            f"  Resolved: {nlu_results['resolved_query']}\n"
            f"  Keywords: {nlu_results['search_keywords']}"
        )

        return {
            "query": nlu_results["query"],
            "original_raw_query": nlu_results["original_raw_query"],
            "user_intent": nlu_results["user_intent"],
            "subject": final_subject,
            "resolved_query": nlu_results["resolved_query"],
            "search_keywords": nlu_results["search_keywords"]
        }
    except Exception as e:
        logger.error(f"Router Node: NLU pipeline failed: {e}", exc_info=True)
        return {
            "subject": "GENERAL",
            "user_intent": "INITIAL_SOLVE",
            "resolved_query": query,
            "search_keywords": query
        }
