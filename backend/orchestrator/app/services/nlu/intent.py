"""
Intent Classification & Structured Answer Extraction Engine for Elementary STEM Socratic Chatbot.
- Structured Gemini 2.5 Flash intent classifier returning JSON adhering to StudentIntent.
- Structured core answer extractor cleaning conversational filler ('I think 12' -> '12').
- High-speed deterministic fallback heuristic for offline/sub-millisecond evaluation (<1ms).
- Off-topic distraction detector and Socratic redirection prompt generator (Day 12).
"""

import os
import re
import asyncio
from typing import Optional, Dict, Any, Union, List
from enum import Enum
from pydantic import BaseModel, Field
from app.services.prompts import prompt_controller
from app.services.nlu.normalizer import normalize_text_sync

class IntentType(str, Enum):
    INITIAL_SOLVE = "INITIAL_SOLVE"
    STEP_ATTEMPT = "STEP_ATTEMPT"
    CLARIFY = "CLARIFY"
    REQUEST_PRACTICE = "REQUEST_PRACTICE"
    CHITCHAT = "CHITCHAT"
    OFF_TOPIC = "OFF_TOPIC"

class IntentResult(BaseModel):
    intent: IntentType = Field(..., description="Classified Intent Label")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Confidence Score 0.0 - 1.0")
    extracted_answer: Optional[str] = Field(default=None, description="Cleaned core answer if intent is STEP_ATTEMPT (e.g. '12', 'chloroplast')")
    raw_response: Optional[str] = None

# Fast-path greeting, identity, and casual phrases
_CHITCHAT_RE = re.compile(
    r'^(?:'
    r'hi|hello|hey|greetings|good\s+(?:morning|afternoon|evening)|'
    r'thanks(?:\s+(?:a\s+lot|so\s+much|very\s+much))?|'
    r'thank\s+you(?:\s+(?:so\s+much|very\s+much))?|'
    r'thx|ty|tysm|bye|goodbye|see\s+ya|cya|'
    r'what(?:\'s|\s+is|\s+ur|\s+your)\s+name|'
    r'who\s+(?:are|r)\s+(?:you|u)|'
    r'how\s+(?:are|r)\s+(?:you|u)(?:\s+doing)?|'
    r'what\s+can\s+you\s+do|'
    r'tell\s+me\s+about\s+yourself|'
    r'what\s+are\s+you|'
    r'who\s+is\s+reanmore|'
    r'what\s+is\s+reanmore'
    r')'
    r'(?:\s+(?:there|tutor|bot|teacher|friend|ai|reanmore))?[\s!.\?]*$',
    flags=re.IGNORECASE
)

# Help & stuck expressions
_HELP_SEEKING_RE = re.compile(
    r'^(?:'
    r'idk|'
    r'i\s+(?:do\s+not|don\'?t|dont)\s+know|'
    r'i\s+(?:do\s+not|don\'?t|dont)\s+understand(?:\s+this\s+step)?|'
    r'i\s+(?:do\s+not|don\'?t|dont)\s+get\s+it|'
    r'help(?:\s+me)?|'
    r'hint(?:\s+please)?|'
    r'give\s+me\s+a\s+hint|'
    r'can\s+i\s+have\s+a\s+hint|'
    r'clue(?:\s+please)?|'
    r'give\s+me\s+a\s+clue|'
    r'what\s+(?:do\s+i\s+do|should\s+i\s+do|should\s+i\s+calculate|next|to\s+do)(?:\s+next)?|'
    r'i\'?m\s+stuck|'
    r'im\s+stuck|'
    r'not\s+sure|'
    r'i\s+need\s+help|'
    r'can\s+you\s+help(?:\s+me)?|'
    r'no\s+idea'
    r')[\s!.\?]*$',
    flags=re.IGNORECASE
)

# Off-topic gaming, internet pop culture, and AI personal questions
_OFF_TOPIC_RE = re.compile(
    r'(?:'
    r'fortnite|roblox|minecraft|brawl\s+stars|pokemon|pokémon|fifa|gta|among\s+us|'
    r'play\s+(?:a\s+)?game|video\s+game|gamer|'
    r'mrbeast|mr\s+beast|tiktok|tik\s+tok|youtube|youtuber|skibidi|anime|taylor\s+swift|'
    r'are\s+you\s+(?:a\s+)?(?:real\s+)?(?:human|robot|ai|person|living|alive)|'
    r'are\s+you\s+real|'
    r'how\s+old\s+are\s+you|what\s+is\s+your\s+age|'
    r'where\s+do\s+you\s+live|who\s+made\s+you|who\s+created\s+you|'
    r'do\s+you\s+have\s+(?:a\s+)?(?:girlfriend|boyfriend|friends|feelings)|'
    r'tell\s+me\s+a\s+(?:bedtime\s+)?story|write\s+(?:me\s+)?a\s+poem'
    r')',
    flags=re.IGNORECASE
)

def get_off_topic_redirection_prompt(
    current_step: Optional[Dict[str, Any]] = None,
    grade_level: str = "grade_4_6",
) -> str:
    """
    Generates a playful, encouraging redirection prompt to guide elementary
    students back to their math or science learning.
    """
    has_step = bool(
        current_step
        and (
            current_step.get("question")
            or current_step.get("step_number")
            or current_step.get("expected_answer")
        )
    )
    is_early_elementary = "1_3" in str(grade_level).lower()

    if has_step:
        if is_early_elementary:
            return "That sounds fun, but let's finish our puzzle first! What number or word do you think is next?"
        return "Haha, that's cool, but let's stay focused on our problem for now! What do you think is the answer to this step?"
    else:
        if is_early_elementary:
            return "Haha, I love games and stories, but my superpower is science and math! What fun question shall we solve?"
        return "I'd love to chat about that, but I'm your math and science buddy! What problem or concept would you like to explore today?"


async def generate_off_topic_redirection_llm(
    query: str,
    current_step: Optional[Dict[str, Any]] = None,
    grade_level: str = "grade_4_6",
) -> str:
    """
    Uses Gemini Flash to generate a personalized Socratic redirection response.
    Uses dynamic prompt templates from PromptController with offline/timeout fallback.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return get_off_topic_redirection_prompt(current_step, grade_level)

    prompt = prompt_controller.get_off_topic_redirection_prompt(
        query=query,
        current_step=current_step,
        grade_level=grade_level,
    )

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        async def _call():
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-3.6-flash",
                    contents=prompt
                )
            )
            return resp.text.strip()

        return await asyncio.wait_for(_call(), timeout=1.5)
    except Exception:
        return get_off_topic_redirection_prompt(current_step, grade_level)


# Clarification question patterns
_CLARIFY_RE = re.compile(
    r'^(?:what\s+(?:is|are|does)|why\s+(?:is|are|does|do)|how\s+(?:does|do|can)|explain|define)\b',
    flags=re.IGNORECASE
)

# Interrogative and question patterns (e.g. "What comes after 19?", "How many...", ending in ?)
_QUESTION_STARTERS_RE = re.compile(
    r'^(?:what|which|how|why|when|where|who|can|could|will|tell\s+me|calculate|solve|find)\b|\?$',
    flags=re.IGNORECASE
)

# Math questions and numerical sequence inquiries (e.g. "What comes after 19?")
_MATH_QUESTION_RE = re.compile(
    r'\b(?:what\s+comes\s+after|what\s+comes\s+before|what\s+is\s+next|next\s+number|count\s+(?:up|down|backward|forward)|how\s+many|how\s+much)\b',
    flags=re.IGNORECASE
)

# Practice request patterns
_PRACTICE_RE = re.compile(
    r'\b(?:another\s+one|more\s+practice|practice\s+problem|give\s+me\s+another|next\s+question)\b',
    flags=re.IGNORECASE
)

# Conversational hedging and answer prefixes
_ANSWER_PREFIXES = re.compile(
    r'^(?:'
    r'i\s+(?:think|believe|guess)(?:\s+(?:that|the\s+answer\s+is|it\s+is|it\'?s))?|'
    r'the\s+answer\s+(?:is|might\s+be|could\s+be)|'
    r'it\s+(?:happens\s+in\s+the|happens\s+in|is\s+in\s+the|is\s+in|is|was|\'s)|'
    r'(?:could|might)\s+it\s+be|'
    r'is\s+it|'
    r'maybe\s+it\s+is|'
    r'maybe|'
    r'probably|'
    r'what\s+about|'
    r'how\s+about'
    r')\s+',
    flags=re.IGNORECASE
)


def is_step_active(current_step: Optional[Dict[str, Any]]) -> bool:
    """
    Checks whether current_step represents an active tutoring step in progress.
    Returns True if current_step is a non-empty dict and not flagged inactive.
    """
    if not current_step or not isinstance(current_step, dict):
        return False
    if current_step.get("active") is False:
        return False
    return any(v is not None and v != "" for v in current_step.values())


def extract_core_answer(text: str) -> Optional[str]:
    """
    Cleans conversational hedging, intros, and trailing punctuation from student answer attempts:
    - 'I think the answer is 12 cookies' -> '12'
    - 'It happens in the chloroplast' -> 'chloroplast'
    - 'Maybe 3/4?' -> '3/4'
    - 'Is it 5?' -> '5'
    - 'Could it be 15 km/h?' -> '15 km/h'
    """
    if not text or not text.strip():
        return None

    cleaned = text.strip()

    # 1. Normalize numbers and units first (e.g. "5cm" -> "5 cm")
    cleaned = normalize_text_sync(cleaned)

    # 2. Strip leading hedging phrases iteratively
    for _ in range(2):
        cleaned = _ANSWER_PREFIXES.sub('', cleaned).strip()

    # 3. Strip trailing punctuation often used in hedging ('?', '!', '.')
    cleaned = re.sub(r'[\?!.]+$', '', cleaned).strip()

    # 4. If answer is numeric with unit words (e.g. "12 cookies" or "12 apples")
    match_num_units = re.match(
        r'^(\d+(?:\.\d+)?(?:/\d+)?)\s+(?:apples?|cookies?|candies?|students?|oranges?)$',
        cleaned,
        flags=re.IGNORECASE
    )
    if match_num_units:
        return match_num_units.group(1)

    return cleaned if cleaned else None


def disambiguate_step_input(
    query: str,
    current_step: Optional[Dict[str, Any]] = None,
    history: Optional[Union[str, List[Dict[str, Any]]]] = None,
    rolling_summary: Optional[str] = None
) -> Optional[IntentResult]:
    """
    Step Context Disambiguation Engine:
    Disambiguates short, single-token student answers and help-seeking phrases
    when an active tutoring step is in progress.
    Returns IntentResult if disambiguated, or None if outside step disambiguation.
    """
    if not is_step_active(current_step):
        return None

    q = (query or "").strip()
    if not q:
        return IntentResult(intent=IntentType.CHITCHAT, confidence=0.5)

    # 1. Greetings & Pleasantries during active step
    if _CHITCHAT_RE.match(q):
        return IntentResult(intent=IntentType.CHITCHAT, confidence=0.98)

    # 2. Help & Stuck expressions during active step -> CLARIFY
    if _HELP_SEEKING_RE.match(q):
        return IntentResult(intent=IntentType.CLARIFY, confidence=0.95)

    # 3. Practice Requests
    if _PRACTICE_RE.search(q):
        return IntentResult(intent=IntentType.REQUEST_PRACTICE, confidence=0.95)

    # 4. Clarification questions (e.g. 'What is a numerator?')
    if _CLARIFY_RE.match(q) and not any(op in q for op in ['+', '-', '*', '/', '=']):
        return IntentResult(intent=IntentType.CLARIFY, confidence=0.90)

    # 4.5. Math inquiry / sequence / new problem question (e.g. "What comes after 19?")
    if _MATH_QUESTION_RE.search(q):
        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.95)

    # 4.6. Off-topic distractions during active step
    if _OFF_TOPIC_RE.search(q) and not re.search(r'\d+\s*[+\-*/=]\s*\d+', q):
        return IntentResult(
            intent=IntentType.OFF_TOPIC,
            confidence=0.95,
            extracted_answer=None,
            raw_response="step_off_topic"
        )

    # 4.7. Standalone math arithmetic expression (e.g. "15 + 27", "8 * 6", "100 - 45", "24 / 6")
    is_fraction_literal = bool(re.match(r'^\s*-?\d+/\d+\s*$', q))
    is_binary_arithmetic = not is_fraction_literal and bool(re.search(r'^\s*\d+(?:\.\d+)?\s*[\+\-\*\/xX×÷]\s*\d+(?:\.\d+)?\s*(?:=\s*\??)?\s*$', q))
    expected_ans = str(current_step.get("expected_answer") or "").strip()
    if is_binary_arithmetic and q != expected_ans:
        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.96)

    # 5. Student answer attempt
    extracted = extract_core_answer(q)
    is_numeric_math = bool(re.match(r'^-?\d+(?:\.\d+)?(?:/\d+)?(?:\s*[a-zA-Z%°/]+)?$', q))
    is_hedged_numeric = bool(_ANSWER_PREFIXES.match(q) and extracted and re.match(r'^-?\d+(?:\.\d+)?(?:/\d+)?(?:\s*[a-zA-Z%°/]+)?$', extracted))
    is_interrogative = bool(_QUESTION_STARTERS_RE.search(q) or q.endswith('?'))

    if is_numeric_math or is_hedged_numeric:
        return IntentResult(
            intent=IntentType.STEP_ATTEMPT,
            confidence=0.95,
            extracted_answer=extracted or q
        )

    # If the user is asking an interrogative question, do NOT treat it as answering the step!
    if is_interrogative:
        has_math_op = any(op in q for op in ['+', '-', '*', '/', '=', '×', '÷'])
        if _CLARIFY_RE.search(q) and not has_math_op:
            return IntentResult(intent=IntentType.CLARIFY, confidence=0.90)
        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.88)

    word_count = len(q.split())
    extracted_word_count = len(extracted.split()) if extracted else 0
    # Conceptual answers are often full short sentences ("It stays in one spot").
    # While a step is active, treat a short declarative message as an attempt.
    # Digit-bearing statements and explicit new-problem requests are excluded so
    # a freshly typed word problem is not swallowed as an answer.
    starts_new_problem = bool(re.match(
        r'^\s*(?:solve|calculate|compute|new\s+problem|another\s+problem)\b',
        q, re.I
    ))
    is_short = (
        (word_count <= 8 and not starts_new_problem and not re.search(r'\d', q))
        or (extracted and extracted_word_count <= 4)
    )
    has_math_op = any(op in q for op in ['+', '-', '*', '/', '=', '×', '÷'])

    if is_short and not has_math_op:
        return IntentResult(
            intent=IntentType.STEP_ATTEMPT,
            confidence=0.90,
            extracted_answer=extracted
        )

    return None


def format_chat_history(
    history: Optional[Union[str, List[Dict[str, Any]]]] = None,
    rolling_summary: Optional[str] = None,
    current_step: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Combines rolling summary, current active step, and recent turns for the intent prompt.
    Accepts either raw turns list, a pre-formatted string, rolling summary, and active step.
    """
    parts = []

    # 1. Include rolling summary if present
    if rolling_summary and rolling_summary.strip():
        parts.append(f"Summary of earlier conversation: {rolling_summary.strip()}")

    # 2. Include active step context if present
    if is_step_active(current_step):
        parts.append(f"Current Active Step: {current_step}")

    # 3. If history is already a formatted string, append directly 
    if isinstance(history, str) and history.strip():
        parts.append(history.strip())
        
    # 4. If history is a list of turns, format the last 6 turns
    elif isinstance(history, list) and history:
        for turn in history[-6:]:
            if "role" in turn:
                speaker = "Student" if turn.get("role") == "user" else "Tutor"
                content = turn.get("content", "")
                parts.append(f"{speaker}: {content}")
            else:
                user_msg = turn.get("user", "")
                bot_msg = turn.get("bot", "")
                if user_msg:
                    parts.append(f"Student: {user_msg}")
                if bot_msg:
                    parts.append(f"Tutor: {bot_msg}")
    return "\n".join(parts) if parts else "No previous conversation history."


def classify_intent_heuristic(
    query: str,
    history: Optional[Union[str, List[Dict[str, Any]]]] = None,
    rolling_summary: Optional[str] = None,
    current_step: Optional[Dict[str, Any]] = None,
) -> IntentResult:
    """
    Fast-path deterministic rule-based fallback (<1ms).
    Used when Gemini API is offline, unconfigured, or times out.
    """
    q = (query or "").strip()
    if not q:
        return IntentResult(intent=IntentType.CHITCHAT, confidence=0.5)

    # 0. Active step disambiguation engine (<1ms)
    if current_step:
        disambiguated = disambiguate_step_input(
            query=q,
            current_step=current_step,
            history=history,
            rolling_summary=rolling_summary,
        )
        if disambiguated is not None:
            return disambiguated

    # 1. Greetings / Pleasantries
    if _CHITCHAT_RE.match(q):
        return IntentResult(intent=IntentType.CHITCHAT, confidence=0.98)

    # 1.5. Off-topic distractions (with word problem protection)
    if _OFF_TOPIC_RE.search(q):
        is_math_word_problem = bool(
            re.search(r'\b(?:how\s+(?:many|much)|calculate|solve|find|total|equals?|plus|minus|times|divided)\b', q, re.IGNORECASE)
            or re.search(r'\d+\s*[+\-*/=]\s*\d+', q)
        )
        if not is_math_word_problem:
            return IntentResult(
                intent=IntentType.OFF_TOPIC,
                confidence=0.95,
                extracted_answer=None,
                raw_response="heuristic_off_topic"
            )

    # 2. Help & Stuck expressions -> CLARIFY
    if _HELP_SEEKING_RE.match(q):
        return IntentResult(intent=IntentType.CLARIFY, confidence=0.95)

    # 3. Practice requests
    if _PRACTICE_RE.search(q):
        return IntentResult(intent=IntentType.REQUEST_PRACTICE, confidence=0.95)

    # 3.5. Conceptual clarification & definition questions
    is_math_calc = bool(re.search(r'\d+\s*[+\-*/=]\s*\d+|\b(?:calculate|solve|how\s+many|how\s+much)\b', q, re.I))
    if not is_math_calc and not any(op in q for op in ['+', '-', '*', '/', '=']):
        if re.search(r'\b(?:mean|meaning|definition|define|explain|what\s+is\s+(?:a|an)\s+\w+|how\s+does\s+\w+\s+work)\b', q, re.I):
            return IntentResult(intent=IntentType.CLARIFY, confidence=0.90)

    has_history = bool(history or (rolling_summary and rolling_summary.strip()))
    # 4. If no conversation history exists yet, it's starting a new question
    if not has_history:
        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.90)

    # 5. Short answer or pure number when history exists -> step attempt
    extracted = extract_core_answer(q)
    is_numeric_math = bool(re.match(r'^-?\d+(?:\.\d+)?(?:/\d+)?(?:\s*[a-zA-Z]+)?$', q))
    is_hedged_numeric = bool(_ANSWER_PREFIXES.match(q) and extracted and re.match(r'^-?\d+(?:\.\d+)?(?:/\d+)?(?:\s*[a-zA-Z]+)?$', extracted))
    is_interrogative = bool(_QUESTION_STARTERS_RE.search(q) or q.endswith('?'))

    if is_numeric_math or is_hedged_numeric:
        return IntentResult(
            intent=IntentType.STEP_ATTEMPT,
            confidence=0.88,
            extracted_answer=extracted or q
        )

    if _MATH_QUESTION_RE.search(q):
        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.90)

    # Standalone math arithmetic expression
    is_fraction_literal = bool(re.match(r'^\s*-?\d+/\d+\s*$', q))
    if not is_fraction_literal and re.search(r'^\s*\d+(?:\.\d+)?\s*[\+\-\*\/xX×÷]\s*\d+(?:\.\d+)?\s*(?:=\s*\??)?\s*$', q):
        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.96)

    has_math_op = not is_fraction_literal and any(op in q for op in ['+', '-', '*', '/', '=', '×', '÷'])
    if not is_interrogative and len(q.split()) <= 4 and not has_math_op:
        return IntentResult(
            intent=IntentType.STEP_ATTEMPT,
            confidence=0.88,
            extracted_answer=extract_core_answer(q)
        )

    # 6. Clarification questions
    if _CLARIFY_RE.match(q) and not any(op in q for op in ['+', '-', '*', '/', '=']):
        return IntentResult(intent=IntentType.CLARIFY, confidence=0.85)

    # Default fallback
    return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.75)


async def classify_intent(
    query: str,
    history: Optional[Union[str, List[Dict[str, Any]]]] = None,
    rolling_summary: Optional[str] = None,
    current_step: Optional[Dict[str, Any]] = None,
) -> IntentResult:
    """
    Classifies student intent using prompt_controller and Gemini Flash.
    Falls back gracefully to deterministic heuristics if offline or timed out.
    """
    # 0. Fast-path deterministic disambiguation (<1ms) if current_step is provided
    if current_step:
        disambiguated = disambiguate_step_input(
            query=query,
            current_step=current_step,
            history=history,
            rolling_summary=rolling_summary,
        )
        if disambiguated is not None:
            return disambiguated

    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return classify_intent_heuristic(query, history, rolling_summary, current_step)

    formatted_history = format_chat_history(
        history=history,
        rolling_summary=rolling_summary,
        current_step=current_step,
    )
    from app.services.guardrails.pii_scrubber import sanitize_for_prompt
    safe_query = sanitize_for_prompt(query)
    prompt = prompt_controller.get_intent_prompt(query=safe_query, chat_history=formatted_history)

    try:
        from google import genai
        client = genai.Client(api_key=api_key)

        async def _call_gemini():
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=prompt
                )
            )
            return resp.text.strip().upper()

        raw_label = await asyncio.wait_for(_call_gemini(), timeout=1.5)

        # Match response against valid IntentType categories
        for valid in IntentType:
            if valid.value in raw_label:
                extracted = extract_core_answer(query) if valid == IntentType.STEP_ATTEMPT else None
                return IntentResult(
                    intent=valid,
                    confidence=0.95,
                    extracted_answer=extracted,
                    raw_response=raw_label
                )

        return IntentResult(intent=IntentType.INITIAL_SOLVE, confidence=0.70, raw_response=raw_label)

    except Exception:
        # Graceful fallback on network error or timeout
        return classify_intent_heuristic(query, history, rolling_summary, current_step)


def classify_intent_sync(
    query: str,
    history: Optional[Union[str, List[Dict[str, Any]]]] = None,
    rolling_summary: Optional[str] = None,
    current_step: Optional[Dict[str, Any]] = None,
) -> IntentResult:
    """Synchronous entrypoint for fast-path intent classification."""
    return classify_intent_heuristic(
        query=query,
        history=history,
        rolling_summary=rolling_summary,
        current_step=current_step,
    )
