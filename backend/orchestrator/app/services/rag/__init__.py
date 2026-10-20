"""
Package: orchestrator/app/services/rag
Description: Curriculum Science RAG service providing local offline embeddings,
             Qdrant vector retrieval, and Socratic context grounding.
"""

from app.services.rag.embedder import FastEmbedClient, get_embedder
from app.services.rag.vector_store import ScienceVectorStore, get_vector_store
from app.services.rag.retriever import ScienceRetriever, get_science_retriever

__all__ = [
    "FastEmbedClient",
    "get_embedder",
    "ScienceVectorStore",
    "get_vector_store",
    "ScienceRetriever",
    "get_science_retriever",
]
