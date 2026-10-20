"""
File: orchestrator/app/services/rag/retriever.py
Description: Socratic Science Retriever orchestrating query embedding,
             vector search with grade-band filtering, and context grounding.
"""

from typing import List, Dict, Any, Optional, Tuple
import logging
from app.services.rag.embedder import FastEmbedClient, get_embedder
from app.services.rag.vector_store import ScienceVectorStore, get_vector_store
from app.services.telemetry.gap_recorder import log_gap_event, record_gap_event

logger = logging.getLogger("reanmore.rag.retriever")

SIMILARITY_THRESHOLD = 0.55


class ScienceRetriever:
    """
    High-level science curriculum retrieval engine.
    Fetches textbook passages and formats them for Socratic prompts.
    """

    def __init__(
        self,
        embedder: Optional[FastEmbedClient] = None,
        vector_store: Optional[ScienceVectorStore] = None,
        min_score: float = SIMILARITY_THRESHOLD
    ):
        self.embedder = embedder or get_embedder()
        self.vector_store = vector_store or get_vector_store()
        self.min_score = min_score

    def retrieve_grounded_context(
        self,
        query: str,
        grade_band: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 3
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """
        Retrieve relevant science passages and generate a formatted context block.
        Synchronous, thread-safe, and safe to call in LangGraph nodes.
        Returns:
            (passages, formatted_context_str, is_grounded)
        """
        if not query or not query.strip():
            return [], "", False

        # 1. Generate local query embedding
        query_vec = self.embedder.embed_query(query)

        # 2. Search Qdrant with grade-level bias
        hits = self.vector_store.search(
            query_vector=query_vec,
            grade_band=grade_band,
            top_k=top_k,
            min_score=self.min_score
        )

        if not hits:
            logger.info(f"No science passages met similarity threshold {self.min_score} for query: '{query}'")
            # Telemetry: Record curriculum content gap synchronously via log_gap_event
            log_gap_event(
                gap_type="content",
                gap_code="SCIENCE_OUT_OF_CURRICULUM",
                severity="warning",
                subject="science",
                grade_tier=grade_band or "grade_1_3",
                session_id=session_id,
                details={
                    "query": query,
                    "reason": "Similarity score below threshold or topic absent from textbook corpus",
                    "threshold": self.min_score,
                }
            )
            return [], "", False

        # 3. Format grounded curriculum context block with citations
        context_lines = ["--- AUTHORITATIVE SCIENCE TEXTBOOK REFERENCE ---"]
        for i, hit in enumerate(hits, 1):
            source = hit.get("source", "Elementary Science Curriculum")
            topic = hit.get("topic", "")
            title = hit.get("title", "")
            text = hit.get("text", "").strip()
            score = hit.get("score", 0.0)
            context_lines.append(f"[{i}] {title} ({topic}) | Source: {source} (Confidence: {score:.2f})")
            context_lines.append(f"    {text}")
        context_lines.append("--------------------------------------------------")

        formatted_context = "\n".join(context_lines)
        return hits, formatted_context, True

    async def retrieve_grounded_context_async(
        self,
        query: str,
        grade_band: Optional[str] = None,
        session_id: Optional[str] = None,
        top_k: int = 3
    ) -> Tuple[List[Dict[str, Any]], str, bool]:
        """Asynchronous wrapper for retrieve_grounded_context."""
        return self.retrieve_grounded_context(
            query=query,
            grade_band=grade_band,
            session_id=session_id,
            top_k=top_k
        )


_retriever_instance: Optional[ScienceRetriever] = None


def get_science_retriever() -> ScienceRetriever:
    """Singleton getter for the science retriever."""
    global _retriever_instance
    if _retriever_instance is None:
        _retriever_instance = ScienceRetriever()
    return _retriever_instance
