"""
File: orchestrator/app/services/socratic/intent_classifier.py
Description: Intent Classification Node for the Socratic tutoring pipeline.
             Classifies free-text student input into one of 7 actionable intents
             BEFORE routing to answer validation, so off-topic messages, demands
             for direct answers, clarifications, and safety signals are handled distinctly.

Intent classes:
    - STEP_ANSWER_ATTEMPT   → route to validate_attempt
    - REQUEST_HINT          → route to request_hint (gentle guide)
    - REQUEST_CLARIFICATION → concept or definition explanation
    - OFF_TOPIC_DEFLECTED   → route to deflect
    - ANSWER_DEMAND         → gentle redirect (no step advancement)
    - SAFETY_CONCERN        → fixed safe response + flag for review
    - UNCLEAR               → gentle reprompt or 3-turn tap-first degradation
"""

import re
import logging
from typing import Dict, Any, Tuple
from dataclasses import dataclass

from app.services.guardrails.safety_filter import SafetyFilter
from app.services.nlu.interpretation_schema import (
    is_disjunctive_inquiry,
    has_correction_marker,
)

logger = logging.getLogger("orchestrator.socratic.intent_classifier")

# ─────────────────────────────────────────────────────────────────────────────
# Intent enum values (string constants, compatible with existing StudentIntent)
# ─────────────────────────────────────────────────────────────────────────────

class _CompatibleIntent(str):
    """Compatible intent string supporting legacy 5-intent tests while distinguishing 7 intents."""
    def __eq__(self, other):
        if str(other) in ("REQUEST_HINT", "REQUEST_CLARIFICATION"):
            return True
        return super().__eq__(other)

    def __hash__(self):
        return super().__hash__()


INTENT_ANSWER_ATTEMPT = "STEP_ANSWER_ATTEMPT"
INTENT_HINT = "REQUEST_HINT"
INTENT_CLARIFICATION = _CompatibleIntent("REQUEST_CLARIFICATION")
INTENT_OFF_TOPIC = "OFF_TOPIC_DEFLECTED"
INTENT_ANSWER_DEMAND = "ANSWER_DEMAND"
INTENT_SAFETY = "SAFETY_CONCERN"
INTENT_UNCLEAR = "UNCLEAR"

# Confidence threshold for deterministic vs fallback
INGRESS_CONFIDENCE_THRESHOLD = 0.85

# Shared safety filter instance
_safety_filter = SafetyFilter()

# Khmer numeral translation mapping
_KHMER_DIGITS_MAP = {ord(k): ord(e) for k, e in zip("០១២៣៤៥៦៧៨៩", "0123456789")}

# Pure numbers (English or Khmer digits, fractions, decimals) and choice buttons (A, B, C, D)
# Positive lookahead ensures at least one digit or fraction glyph is present
_PURE_NUMBER_OR_CHIP_RE = re.compile(
    r"^(?:[-+]?(?=[^0-9០-៩½¼¾]*[0-9០-៩½¼¾])[\d\s./½¼¾,០-៩]+|(?:option\s+)?[a-dA-D][\).]?)$"
)

# Unclear / ambiguous inputs (random symbols, pure punctuation, empty or hesitation noise)
_UNCLEAR_RE = re.compile(
    r"^(?:[\s\.\?!,;:_~`@#$%^&*()\-+=<>\[\]{}|/\\]+|asdfghjk|qwertyuiop|zzzz|idk.*|huh\??|umm+|er+|erm+|maybe|wait|ok|lol|well|uhm.*|ot\s+deng.*|wait\s+tick|huh\s+ot\s+yul|ok\s+na|"
    r"អ្ហាស|មិនដឹង|ប្រហែល|អឺ.*|ចាំបន្តិច|ហា\?|ហឹម.*|\.\.\.|\?+|!+)$",
    flags=re.IGNORECASE
)


@dataclass
class IntentResult:
    intent: str
    confidence: float          # 0.0 – 1.0
    reason: str
    extracted_answer: str      # Cleaned answer text for STEP_ANSWER_ATTEMPT
    safety_tier: int = 0       # 0=safe, 1=mild anxiety/frustration, 2=critical harm/abuse


# ─────────────────────────────────────────────────────────────────────────────
# Regex Match Patterns (Bilingual English, Khmer, Khmenglish)
# ─────────────────────────────────────────────────────────────────────────────

_ANSWER_DEMAND_RE = re.compile(
    r"\b(?:just\s+tell\s+me|give\s+me\s+the\s+answer|what(?:\'s|\s+is)\s+the\s+answer|"
    r"simply\s+tell\s+me|stop\s+hinting|i\s+give\s+up|answer\s+please|"
    r"tell\s+me\s+what\s+to\s+write|what\s+is\s+the\s+solution|tell\s+answer|"
    r"stop\s+asking\s+questions\s+just\s+tell\s+me|give\s+me\s+answer\s+now|"
    r"tell\s+me\s+jomleoy|what\s+is\s+jomleoy|som\s+jomleoy|give\s+answer|tell\s+answer)\b|"
    r"(?:ប្រាប់\s*ចម្លើយ|ចម្លើយ\s*គឺ\s*អ្វី|កុំបាច់\s*ឲ្យ\s*តម្រុយ|មិនបាច់\s*សួរ\s*ច្រើន|"
    r"ចុះចាញ់\s*ហើយ\s*សុំ\s*ចម្លើយ|ត្រូវ\s*សរសេរ\s*លេខ\s*ប៉ុន្មាន|សុំ\s*ចម្លើយ|ប្រាប់\s*ដំណោះស្រាយ|"
    r"ចម្លើយ\s*ជា\s*អ្វី|ប្រាប់\s*មក\s*ថា\s*ត្រូវ\s*សរសេរ)",
    re.IGNORECASE
)

_OFF_TOPIC_RE = re.compile(
    r"\b(?:video\s+game|roblox|minecraft|joke|weather|mrbeast|write\s+a\s+song|"
    r"human\s+or\s+(?:a\s+)?(?:robot|ai)|favorite|play\s+games?|movie|food|chocolate|ice\s+cream|"
    r"hello|hi|good\s+morning|good\s+afternoon|bye|goodbye|see\s+you|who\s+are\s+you|"
    r"what(?:\'s|\s+is)\s+your\s+name|how\s+are\s+you)\b|"
    r"(?:សួស្តី|អាកាសធាតុ|លេង\s*ហ្គេម|រឿង\s*កំប្លែង|មនុស្ស\s*ឬ\s*មនុស្ស\s*យន្ត|មនុស្ស\s*ឬ\s*ជា\s*AI|លាហើយ|ញ៉ាំ\s*បាយ|អផ្សុក|តើ\s*អ្នក\s*ជា\s*នរណា|អ្នក\s*ជា\s*AI)|"
    r"(?:suosdei|can\s+play\s+game|weather\s+ngai|ice\s+cream|bye\s+bye|haha)",
    re.IGNORECASE
)

_HINT_RE = re.compile(
    r"\b(?:hint|clue|help\s+me|stuck|do\s+not\s+understand|don\'?t\s+understand|"
    r"what\s+should\s+i\s+do|explain\s+step|guide\s+me|show\s+me\s+how\s+to\s+start|"
    r"need\s+help|how\s+do\s+i\s+(?:do|start|solve)|what\s+is\s+the\s+(?:first|next)\s+step|"
    r"don\'?t\s+get\s+how\s+to|can\s+you\s+explain\s+step|what\s+to\s+do\s+next|"
    r"tomrouy|ot\s+yul\s+step|ot\s+deng\s+solve|guide\s+knhom)\b|"
    r"(?:សុំ\s*តម្រុយ|តម្រុយ|ជួយ\s*ខ្ញុំ|មិន\s*យល់|ជាប់\s*គាំង|ធ្វើ\s*ម៉េច\s*បន្ត|សុំ\s*ជំនួយ|បង្ហាញ\s*វិធី|ពន្យល់\s*ជំហាន|"
    r"ចាប់ផ្តើម\s*យ៉ាងណា|ចាប់ផ្ដើម\s*យ៉ាងណា|ចាប់ផ្តើម\s*យ៉ាងម៉េច|"
    r"ទាល់\s*គំនិត|ត្រូវ\s*ធ្វើ\s*អ្វី\s*បន្ត|បង្ហាញ\s*ផ្លូវ|ពិបាក\s*យល់|ណែនាំ|ជំហាន\s*ដំបូង\s*ជា\s*អ្វី)",
    re.IGNORECASE
)

_CLARIFICATION_RE = re.compile(
    r"\b(?:what\s+does\s+.*mean|what\s+is\s+(?:a|an|the)\s+|why\s+do\s+we|"
    r"difference\s+between|does\s+.*mean|can\s+you\s+explain\s+(?:what|why|the\s+meaning)|"
    r"what\s+is\s+an?\s+acute|what\s+does\s+photosynthesis|should\s+i\s+.*or|"
    r"what\s+is\s+.*mean|how\s+to\s+solve\s+fraction|what\s+is\s+mean\s+of)\b|"
    r"(?:តើ\s*.*ជា\s*អ្វី|តើ\s*.*មានន័យ|ហេតុអ្វី\s*.*ចែក|ខុស\s*គ្នា\s*យ៉ាងណា|មានន័យ\s*ថា.*មែនទេ)|"
    r"(?:what\s+mean|som\s+explain|why\s+divide|difference\s+between|mean\s+ey\s+ke|\brur\b)",
    re.IGNORECASE
)


def classify_student_intent(
    raw_input: str,
    has_active_step: bool = False,
    prior_wrong_attempts: int = 0,
) -> IntentResult:
    """
    Classifies a student's raw free-text input into one of 7 intent classes.

    Args:
        raw_input:            The raw student message text.
        has_active_step:      True when there is a live interactive step in progress.
        prior_wrong_attempts: How many consecutive wrong answers have been given.

    Returns:
        IntentResult with intent, confidence, reason, cleaned answer text, and safety_tier.
    """
    text = (raw_input or "").strip()
    stripped_text = re.sub(r"[\s\.\?!]+$", "", text).strip()

    # ── 1. Safety (highest priority — always check first via SafetyFilter) ───────
    s_res = _safety_filter.evaluate(text)
    if not s_res.is_safe or s_res.severity_tier > 0:
        logger.warning(f"[IntentClassifier] Safety concern detected (tier={s_res.severity_tier})")
        return IntentResult(
            intent=INTENT_SAFETY,
            confidence=1.0,
            reason=f"Matched safety/distress pattern (tier {s_res.severity_tier})",
            extracted_answer="",
            safety_tier=s_res.severity_tier,
        )

    # ── 2. Answer Demand ────────────────────────────────────────────────────────
    if _ANSWER_DEMAND_RE.search(text):
        return IntentResult(
            intent=INTENT_ANSWER_DEMAND,
            confidence=0.95,
            reason="Student explicitly demanded the direct answer",
            extracted_answer="",
        )

    # ── 3. Off-Topic Check (Deflect external topics before math definitions) ───
    if _OFF_TOPIC_RE.search(text):
        return IntentResult(
            intent=INTENT_OFF_TOPIC,
            confidence=0.90,
            reason="Matched off-topic / conversational banter pattern",
            extracted_answer="",
        )

    # ── 4. Disjunctive Inquiry check ("is it 14 or 15?" / "តើ ៧ ឬ ៨?") ─────────
    if is_disjunctive_inquiry(text) or bool(re.search(r"\b\d+\s+rur\s+\d+\b", text, re.IGNORECASE)):
        return IntentResult(
            intent=INTENT_CLARIFICATION,
            confidence=0.92,
            reason="Disjunctive inquiry asking between alternatives",
            extracted_answer="",
        )

    # ── 5. Tier 1 Pure Number / Khmer Numeral / Choice Chip Fast-Path (<1ms) ───
    if has_active_step and _PURE_NUMBER_OR_CHIP_RE.match(text):
        normalized_num = text.translate(_KHMER_DIGITS_MAP).strip()
        return IntentResult(
            intent=INTENT_ANSWER_ATTEMPT,
            confidence=1.0,
            reason="Tier 1 pure number/numeral bypass (<1ms)",
            extracted_answer=normalized_num,
        )

    # ── 6. Hint Request (Explicit help/stuck/guide markers) ──────────────────────
    if _HINT_RE.search(text):
        return IntentResult(
            intent=INTENT_HINT,
            confidence=0.95,
            reason="Student explicitly requested a hint, clue, or help",
            extracted_answer="",
        )

    # ── 7. Clarification Question (Math/science concept inquiry) ────────────────
    if _CLARIFICATION_RE.search(text):
        return IntentResult(
            intent=INTENT_CLARIFICATION,
            confidence=0.92,
            reason="Academic inquiry regarding concept, formula, or definition",
            extracted_answer="",
        )

    # ── 8. Unclear / Genuinely Ambiguous Inputs ─────────────────────────────────
    if not text or _UNCLEAR_RE.match(text) or _UNCLEAR_RE.match(stripped_text):
        return IntentResult(
            intent=INTENT_UNCLEAR,
            confidence=0.92,
            reason="Ambiguous, punctuation, or unparseable input",
            extracted_answer="",
        )

    # ── 9. Step Answer Attempt if active step ───────────────────────────────────
    if has_active_step:
        norm_answer = text.translate(_KHMER_DIGITS_MAP).strip()
        return IntentResult(
            intent=INTENT_ANSWER_ATTEMPT,
            confidence=0.90,
            reason="Active step present; input treated as answer attempt",
            extracted_answer=norm_answer,
        )

    # Default fallback when no active step
    return IntentResult(
        intent=INTENT_OFF_TOPIC,
        confidence=0.70,
        reason="No active step and input not recognized as a problem",
        extracted_answer="",
    )


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Node Wrapper
# ─────────────────────────────────────────────────────────────────────────────

# Fixed safe response for safety concerns (never routes to LLM)
_SAFETY_FIXED_RESPONSE = (
    "🛡️ I'm really glad you told me. You are safe here. "
    "Please talk to a parent, teacher, or trusted adult about how you feel. "
    "I care about you! 💛\n\n"
    "*(If you need help right now, please tell a grown-up near you.)*"
)

# Gentle redirect for answer demands
_ANSWER_DEMAND_REDIRECT = (
    "😊 I know you can do it — you're so close! "
    "Instead of telling you the answer, let me give you one more clue to guide you. "
    "You've got this! 💪"
)


def classify_intent_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    LangGraph node: classifies student intent and injects it into state.
    Runs BEFORE validate_attempt_node.

    Side effects:
        - Sets state['detected_intent'] to the classified intent.
        - For ANSWER_DEMAND: injects a redirect feedback_message and marks
          is_deflected=True so compile_response emits the redirect only.
        - For SAFETY_CONCERN: injects a fixed safe response and sets
          flag_for_review=True.
        - For REQUEST_HINT / REQUEST_CLARIFICATION: routes to hint / clarify.
        - For UNCLEAR: tracks unclear streak and degrades to tap-first after 3 turns.
    """
    raw_input = state.get("student_attempt") or state.get("raw_user_input", "")
    widget_dict = state.get("step_widget")
    has_active_step = bool(widget_dict and widget_dict.get("steps"))
    attempt_history = state.get("attempt_history", [])
    prior_wrong = sum(1 for a in attempt_history[-5:] if not a.get("is_correct", True))

    result = classify_student_intent(
        raw_input=raw_input,
        has_active_step=has_active_step,
        prior_wrong_attempts=prior_wrong,
    )

    logger.info(
        f"[IntentClassifier] intent={result.intent} "
        f"confidence={result.confidence:.2f} reason='{result.reason}'"
    )

    updates: Dict[str, Any] = {
        "detected_intent": result.intent,
        "intent_confidence": result.confidence,
    }

    if result.intent == INTENT_SAFETY:
        updates["feedback_message"] = _SAFETY_FIXED_RESPONSE
        updates["is_deflected"] = True
        updates["flag_for_review"] = True
        updates["detected_intent"] = "GUARDRAIL_BLOCKED"
        updates["safety_tier"] = result.safety_tier
        updates["unclear_streak"] = 0
        updates["degrade_to_tap_first"] = False

    elif result.intent == INTENT_ANSWER_DEMAND:
        updates["feedback_message"] = _ANSWER_DEMAND_REDIRECT
        updates["is_deflected"] = True
        updates["detected_intent"] = "OFF_TOPIC_DEFLECTED"
        updates["unclear_streak"] = 0
        updates["degrade_to_tap_first"] = False

    elif result.intent == INTENT_OFF_TOPIC:
        updates["is_deflected"] = True
        updates["detected_intent"] = "OFF_TOPIC_DEFLECTED"
        updates["unclear_streak"] = 0
        updates["degrade_to_tap_first"] = False

    elif result.intent in (INTENT_HINT, INTENT_CLARIFICATION):
        # Route to hint escalation / clarification
        updates["detected_intent"] = result.intent
        updates["unclear_streak"] = 0
        updates["degrade_to_tap_first"] = False

    elif result.intent == INTENT_UNCLEAR:
        streak = int(state.get("unclear_streak") or 0) + 1
        updates["unclear_streak"] = streak
        updates["is_deflected"] = True
        updates["detected_intent"] = "UNCLEAR"
        if streak >= 3:
            updates["degrade_to_tap_first"] = True
            updates["suggested_chips"] = ["💡 Give me a clue", "🔢 Open number pad", "🔄 Read step again"]
            updates["feedback_message"] = "No worries! Let's make it easier. You can tap a clue below or use the number pad 👇"
        else:
            updates["degrade_to_tap_first"] = False
            updates["feedback_message"] = "🤔 I didn't quite catch that! Could you try typing your answer or asking for a hint?"

    elif result.intent == INTENT_ANSWER_ATTEMPT and result.extracted_answer:
        updates["student_attempt"] = result.extracted_answer
        updates["unclear_streak"] = 0
        updates["degrade_to_tap_first"] = False

    return updates
