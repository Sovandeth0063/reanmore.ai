"""
File: orchestrator/app/services/nlu/context_cache.py
Description: Thread-Safe Contextual LRU Cache with TTL and Intent Gating (Sprint 3 - Task 3.1).
             Caches context-independent queries (e.g., standard definitions, chitchat).
             Explicitly bypasses answer attempts, hint requests, safety concerns, and unclear noise.

Cache Key Specification:
    sha256(f"{normalized_text}:{step_type}:{subject}:{language}").hexdigest()
"""

import time
import hashlib
import threading
from collections import OrderedDict
from typing import Any, Optional, Dict, Tuple


# Set of intents that are safe and context-independent to cache
CACHEABLE_INTENTS = {
    "OFF_TOPIC_DEFLECTED",
    "OFF_TOPIC",
    "CHITCHAT",
    "GREETING",
    "CONCEPT_INQUIRY",
    "META_QUESTION",
}

# Intents that depend on live pedagogical state, safety assessment, or hint tiers
NON_CACHEABLE_INTENTS = {
    "STEP_ANSWER_ATTEMPT",
    "REQUEST_HINT",
    "SAFETY_CONCERN",
    "GUARDRAIL_BLOCKED",
    "ANSWER_DEMAND",
    "UNCLEAR",
}


def is_cacheable_intent(intent: Optional[str]) -> bool:
    """
    Returns True ONLY if the intent is context-independent and safe to cache.
    Answer attempts, hints, safety signals, and unclear inputs return False.
    """
    if not intent:
        return False
    norm = intent.strip().upper()
    if norm in NON_CACHEABLE_INTENTS:
        return False
    return norm in CACHEABLE_INTENTS


def generate_context_cache_key(
    normalized_text: str,
    step_type: Optional[str] = None,
    subject: Optional[str] = None,
    language: Optional[str] = None,
) -> str:
    """
    Computes a deterministic SHA-256 hash composite key combining text and context.
    
    Format:
        sha256(f"{normalized_text}:{step_type}:{subject}:{language}").hexdigest()
    """
    clean_text = (normalized_text or "").strip().lower()
    clean_step = (step_type or "none").strip().lower()
    clean_subj = (subject or "general").strip().lower()
    clean_lang = (language or "unknown").strip().lower()

    raw_composite = f"{clean_text}:{clean_step}:{clean_subj}:{clean_lang}"
    return hashlib.sha256(raw_composite.encode("utf-8")).hexdigest()


class ContextCache:
    """
    Thread-safe, bounded LRU Cache with TTL support and intent gating.
    """

    def __init__(self, max_size: int = 1024, default_ttl_seconds: Optional[int] = 3600):
        self.max_size = max(1, max_size)
        self.default_ttl = default_ttl_seconds
        self._cache: OrderedDict[str, Tuple[Any, Optional[float]]] = OrderedDict()
        self._lock = threading.Lock()
        
        # Operational Telemetry
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._bypasses = 0

    def get(self, key: str) -> Optional[Any]:
        """
        Retrieves a value from cache by key.
        Evicts expired items and moves accessed item to most-recent position.
        """
        with self._lock:
            if key not in self._cache:
                self._misses += 1
                return None

            value, expires_at = self._cache[key]
            
            # Check TTL expiry
            if expires_at is not None and time.time() > expires_at:
                del self._cache[key]
                self._misses += 1
                return None

            # Move to end to mark as recently used (LRU policy)
            self._cache.move_to_end(key)
            self._hits += 1
            return value

    def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: Optional[int] = None,
        intent: Optional[str] = None,
    ) -> bool:
        """
        Sets a key-value pair in cache if intent is cacheable (or intent not provided).
        Returns True if stored, False if bypassed.
        """
        if intent is not None and not is_cacheable_intent(intent):
            with self._lock:
                self._bypasses += 1
            return False

        effective_ttl = ttl_seconds if ttl_seconds is not None else self.default_ttl
        expires_at = (time.time() + effective_ttl) if effective_ttl else None

        with self._lock:
            if key in self._cache:
                self._cache.move_to_end(key)
            self._cache[key] = (value, expires_at)

            # Evict oldest entry if capacity exceeded
            if len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
                self._evictions += 1
            return True

    def clear(self) -> None:
        """Purges all entries from the cache."""
        with self._lock:
            self._cache.clear()

    def size(self) -> int:
        """Returns the current number of cached entries."""
        with self._lock:
            return len(self._cache)

    def stats(self) -> Dict[str, int]:
        """Returns cache telemetry stats."""
        with self._lock:
            return {
                "size": len(self._cache),
                "max_size": self.max_size,
                "hits": self._hits,
                "misses": self._misses,
                "evictions": self._evictions,
                "bypasses": self._bypasses,
            }
