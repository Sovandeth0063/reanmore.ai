"""
File: backend/testing/unit/rag/test_science_rag.py
Description: Unit test suite for Phase 3 Curriculum Science RAG subsystem.
             Verifies:
             1. Offline FastEmbed client initialization and 384-dim embedding.
             2. ScienceVectorStore collection indexing and search.
             3. ScienceRetriever context grounding and textbook citations.
             4. Content gap dispatch for out-of-curriculum queries.
             5. Socratic LangGraph integration with science grounding.
"""

import pytest
import os
from typing import Dict, Any

from app.services.rag.embedder import FastEmbedClient, get_embedder
from app.services.rag.vector_store import ScienceVectorStore, get_vector_store
from app.services.rag.retriever import ScienceRetriever, get_science_retriever
from app.services.telemetry.gap_recorder import get_gap_recorder
from app.services.socratic.graph import build_socratic_graph
from langgraph.checkpoint.memory import MemorySaver


class TestScienceRAGSubsystem:

    def test_fastembed_offline_embeddings(self):
        """Verify FastEmbed client produces normalized 384-dimensional vectors."""
        embedder = get_embedder()
        assert embedder.expected_dim == 384

        vec = embedder.embed_query("What are the parts of a plant?")
        assert len(vec) == 384
        # Cosine normalized vectors have magnitude close to 1.0
        norm = sum(x**2 for x in vec) ** 0.5
        assert abs(norm - 1.0) < 1e-2

    def test_vector_store_retrieval_accuracy(self):
        """Verify Qdrant similarity search returns relevant science chapters."""
        store = get_vector_store()
        embedder = get_embedder()

        query = "How do green plants make food with sunlight?"
        query_vec = embedder.embed_query(query)
        hits = store.search(query_vec, top_k=2, min_score=0.65)

        assert len(hits) >= 1
        top_hit = hits[0]
        assert "Photosynthesis" in top_hit["title"] or "Plant" in top_hit["title"]
        assert top_hit["subject"] == "science"
        assert top_hit["score"] >= 0.70

    def test_science_retriever_grounded_context_format(self):
        """Verify ScienceRetriever formats textbook passages with citations."""
        retriever = get_science_retriever()
        hits, context_str, is_grounded = retriever.retrieve_grounded_context(
            query="What happens when ice melts?",
            grade_band="grade_1_3"
        )

        assert is_grounded is True
        assert len(hits) >= 1
        assert "AUTHORITATIVE SCIENCE TEXTBOOK REFERENCE" in context_str
        assert "Source:" in context_str
        assert "Heating and Cooling" in context_str or "States of Matter" in context_str

    @pytest.mark.asyncio
    async def test_out_of_curriculum_deflection_and_gap_logging(self):
        """Verify queries outside elementary science curriculum log a content gap event."""
        import asyncio
        recorder = get_gap_recorder()
        recorder.clear_memory_buffer()

        retriever = get_science_retriever()
        hits, context_str, is_grounded = retriever.retrieve_grounded_context(
            query="How do I build a nuclear reactor with enriched uranium?",
            grade_band="grade_1_3",
            session_id="test_rag_session_gap"
        )

        assert is_grounded is False
        assert len(hits) == 0
        assert context_str == ""

        # Yield to event loop for non-blocking task execution
        await asyncio.sleep(0.05)

        # Verify content gap event was logged in memory buffer
        events = recorder.get_memory_events()
        gap_events = [e for e in events if e.get("gap_code") == "SCIENCE_OUT_OF_CURRICULUM"]
        assert len(gap_events) >= 1
        assert gap_events[-1]["gap_type"] == "content"
        assert gap_events[-1]["subject"] == "science"

    @pytest.mark.asyncio
    async def test_socratic_graph_science_grounding(self):
        """Verify LangGraph initial_problem produces 2-4 step cards with retrieved_context."""
        graph = build_socratic_graph(checkpointer=MemorySaver())
        config = {"configurable": {"thread_id": "test_science_rag_graph"}}

        result = await graph.ainvoke({
            "session_id": "test_science_rag_graph",
            "raw_user_input": "Why do plants have roots and leaves?",
            "problem_text": "Why do plants have roots and leaves?",
            "subject": "science",
            "grade_level": "grade_1_3",
            "detected_intent": "INITIAL_QUESTION"
        }, config=config)

        assert result["is_problem_complete"] is False
        assert "step_widget" in result
        assert result["step_widget"] is not None
        steps = result["step_widget"]["steps"]
        assert len(steps) >= 2

        # Verify science grounding context and citations were attached
        assert "retrieved_context" in result
        assert len(result.get("retrieved_context", "")) > 0
        assert "Plant Structure and Functions" in result["retrieved_context"]
        assert "curriculum_citations" in result
        assert len(result.get("curriculum_citations", [])) >= 1
