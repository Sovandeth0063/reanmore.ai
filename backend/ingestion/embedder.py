"""
File: backend/ingestion/embedder.py
Description: Embedding engine using Google GenAI SDK (text-embedding-004, 768 dims)
             with batch processing and dry-run fallback.
"""

from __future__ import annotations
import os
import time
import logging
from typing import List
import numpy as np

logger = logging.getLogger("ingestion.embedder")


class EmbeddingEngine:
    """
    Generates 768-dimensional embeddings for curriculum text chunks.
    Uses Google GenAI text-embedding-004 by default.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "models/text-embedding-004",
        expected_dim: int = 768,
        dry_run: bool = False
    ):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY", "")
        self.model_name = model_name
        self.expected_dim = expected_dim
        self.dry_run = dry_run
        self._client = None

    def _get_client(self):
        if self._client is None and not self.dry_run:
            if not self.api_key:
                logger.warning(
                    "GEMINI_API_KEY not configured. Running embedder in mock/offline mode."
                )
                self.dry_run = True
                return None
            try:
                from google import genai
                self._client = genai.Client(api_key=self.api_key)
            except Exception as e:
                logger.error(f"Failed to initialize google.genai Client: {e}")
                self.dry_run = True
        return self._client

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a batch of texts into 768-dim vectors.
        """
        if not texts:
            return []

        if self.dry_run:
            # Deterministic pseudo-vector for dry-run validation without calling API
            results = []
            for t in texts:
                # Seed random generator with string hash for reproducible mock vector
                h = abs(hash(t)) % (2**32)
                np.random.seed(h)
                vec = np.random.normal(0, 1, self.expected_dim)
                vec = vec / np.linalg.norm(vec)
                results.append(vec.tolist())
            return results

        client = self._get_client()
        if client is None:
            # Fall back to dry-run mock vectors if client couldn't be initialized
            return self.embed_texts(texts)

        # Process in chunks of 50 to avoid API payload limits
        chunk_batch_size = 50
        all_embeddings: List[List[float]] = []

        for i in range(0, len(texts), chunk_batch_size):
            batch = texts[i : i + chunk_batch_size]
            retries = 3
            backoff = 1.0

            while retries > 0:
                try:
                    response = client.models.embed_content(
                        model=self.model_name,
                        contents=batch,
                    )
                    # response.embeddings is a list of ContentEmbedding objects with .values
                    for emb in response.embeddings:
                        values = list(emb.values)
                        all_embeddings.append(values)
                    break
                except Exception as e:
                    retries -= 1
                    logger.warning(
                        f"Embedding error on batch {i//chunk_batch_size}: {e}. Retries left: {retries}"
                    )
                    if retries > 0:
                        time.sleep(backoff)
                        backoff *= 2
                    else:
                        raise RuntimeError(f"Embedding failed after 3 retries: {e}")

        return all_embeddings
