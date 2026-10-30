"""
File: services/science_service/app/validator.py
Description: Conceptual and semantic keyword validator for elementary & middle school science topics.
             Handles synonyms, stem matching, token overlap, and conceptual equivalence.
"""

import re
from typing import Optional

SCIENCE_SYNONYMS = {
    "evaporation": [
        "evaporate", "evaporates", "evaporating", "vaporization", "steam",
        "liquid to gas", "water vapor", "turns into gas", "turns to vapor", "liquid turns into gas"
    ],
    "condensation": [
        "condense", "condenses", "condensing", "gas to liquid", "water droplets",
        "dew", "clouds form", "steam turns to water"
    ],
    "precipitation": [
        "rain", "snow", "sleet", "hail", "falling water"
    ],
    "photosynthesis": [
        "making food using sunlight", "sunlight and water", "chloroplast",
        "produce glucose", "light energy to chemical energy", "plants make food",
        "plants make food using sunlight"
    ],
    "gravity": [
        "gravitational force", "pull of earth", "weight", "falling down",
        "pulls down", "gravity pulls it down", "force of gravity"
    ],
    "friction": [
        "rubbing", "resistance to motion", "slows down", "opposes motion"
    ],
    "mitochondria": [
        "powerhouse", "powerhouse of the cell", "cellular respiration", "energy maker",
        "produces atp", "cellular energy"
    ],
    "chloroplast": [
        "green pigment", "chlorophyll", "photosynthesis organelle", "makes food for plant"
    ],
    "solid": [
        "ice", "fixed shape", "rigid"
    ],
    "liquid": [
        "water", "flows", "takes shape of container"
    ],
    "gas": [
        "steam", "air", "vapor", "expands"
    ]
}


def verify_science_concept(student_attempt: str, expected_concept: str) -> bool:
    """
    Checks conceptual equivalence:
    1. Direct or normalized text match
    2. Substring containment
    3. Known scientific synonym groups
    4. Token overlap (ignoring common stopwords)
    """
    if not student_attempt or not expected_concept:
        return False

    s_clean = student_attempt.strip().lower()
    e_clean = expected_concept.strip().lower()

    # 1. Fast-path checks:
    # - Exact match: s_clean == e_clean (e.g. "evaporation" == "evaporation")
    # - Sentence match: e_clean in s_clean (e.g. "the answer is evaporation" contains "evaporation")
    if s_clean == e_clean or e_clean in s_clean:
        return True

    # Check bounded full-word keyword match in expected (avoiding sub-word substrings like "is" in "photosynthesis")
    common_stopwords = {"the", "a", "an", "is", "it", "to", "of", "and", "in", "by", "for", "that", "its", "into", "on", "at", "no", "yes"}
    if len(s_clean) >= 3 and s_clean not in common_stopwords:
        if re.search(rf'\b{re.escape(s_clean)}\b', e_clean):
            return True

    # Check synonym dictionary
    for concept, synonyms in SCIENCE_SYNONYMS.items():
        all_variants = [concept] + synonyms
        student_matches = any(syn in s_clean for syn in all_variants)
        expected_matches = any(syn in e_clean for syn in all_variants)
        if student_matches and expected_matches:
            return True

    # Token overlap check (ignoring stopwords)
    stopwords = {"the", "a", "an", "is", "it", "to", "of", "and", "in", "by", "for", "that", "its", "into"}
    s_tokens = set(re.findall(r'\b\w+\b', s_clean)) - stopwords
    e_tokens = set(re.findall(r'\b\w+\b', e_clean)) - stopwords

    if s_tokens and e_tokens:
        overlap = s_tokens.intersection(e_tokens)
        if len(overlap) / max(len(e_tokens), 1) >= 0.5:
            return True

    return False
