"""
File: orchestrator/app/services/rag/embedder.py
Description: 100% offline local embedding client using FastEmbed ONNX runtime.
             Model: BAAI/bge-small-en-v1.5 (384 dims, fast CPU execution, $0.00 cost).
"""

from typing import List, Optional
import logging
import numpy as np

logger = logging.getLogger("reanmore.rag.embedder")


class FastEmbedClient:
    """
    Local CPU-based embedding client backed by FastEmbed.
    Generates 384-dimensional cosine-normalized embeddings.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5", expected_dim: int = 384):
        self.model_name = model_name
        self.expected_dim = expected_dim
        self._model = None

    def _get_model(self):
        if self._model is None:
            try:
                from fastembed import TextEmbedding
                self._model = TextEmbedding(model_name=self.model_name)
                logger.info(f"Loaded FastEmbed model: {self.model_name} (dim: {self.expected_dim})")
            except Exception as e:
                logger.error(f"Failed to load FastEmbed model {self.model_name}: {e}")
                raise RuntimeError(f"FastEmbed initialization error: {e}")
        return self._model

    def embed_query(self, text: str) -> List[float]:
        """Embed a single search query."""
        if not text or not text.strip():
            return [0.0] * self.expected_dim
        model = self._get_model()
        # FastEmbed embed() returns a generator of numpy arrays
        embeddings = list(model.embed([text]))
        return embeddings[0].tolist()

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed a batch of document passages."""
        if not texts:
            return []
        model = self._get_model()
        embeddings = list(model.embed(texts))
        return [emb.tolist() for emb in embeddings]


_embedder_instance: Optional[FastEmbedClient] = None


def get_embedder() -> FastEmbedClient:
    """Singleton getter for the offline embedder."""
    global _embedder_instance
    if _embedder_instance is None:
        _embedder_instance = FastEmbedClient()
    return _embedder_instance
