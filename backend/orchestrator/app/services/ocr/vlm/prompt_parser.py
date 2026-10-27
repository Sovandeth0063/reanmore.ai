"""
Shared precision prompt + parser for all VLM providers.

The prompt instructs the model to return a strict JSON schema capturing
every printed and handwritten element, bounding boxes (0-1000 scale),
student answers, figure descriptions, and match connections.
"""
from __future__ import annotations

import json
import logging
import re
from typing import Any, Optional

from app.services.ocr.schemas.homework import (
    Page, Section, Question, QuestionType,
    HomeworkHeader, SignatureBox, Direction, Footer,
    FigureInfo, AnswerAreaEntry, TextElement, MatchingElement,
    ReviewFlag, ReviewReason, LayoutRegion, ElementType,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Question-type normalisation
# ---------------------------------------------------------------------------
_TYPE_MAP: dict[str, QuestionType] = {
    "fill_blank":       QuestionType.FILL_BLANK,
    "equation":         QuestionType.MATH_EQUATION,
    "match":            QuestionType.MATCHING,
    "circle":           QuestionType.CIRCLE,
    "tick":             QuestionType.TICK,
    "table":            QuestionType.TABLE,
    "draw":             QuestionType.DRAW,
    "order":            QuestionType.ORDERING,
    "multiple_choice":  QuestionType.MULTIPLE_CHOICE,
    "short_answer":     QuestionType.SHORT_ANSWER,
    "other":            QuestionType.OTHER,
    # legacy aliases
    "fill_in_blank":    QuestionType.FILL_BLANK,
    "math_equation":    QuestionType.MATH_EQUATION,
    "matching":         QuestionType.MATCHING,
    "long_answer":      QuestionType.SHORT_ANSWER,
    "word_bank":        QuestionType.FILL_BLANK,
    "true_false":       QuestionType.MULTIPLE_CHOICE,
    "visual_counting":  QuestionType.CIRCLE,
    "label_diagram":    QuestionType.DRAW,
    "ordering":         QuestionType.ORDERING,
    "unknown":          QuestionType.UNKNOWN,
}


def _norm_qtype(raw: str) -> QuestionType:
    return _TYPE_MAP.get(str(raw).lower().strip(), QuestionType.UNKNOWN)


# ---------------------------------------------------------------------------
# Answer area kind normalisation
# ---------------------------------------------------------------------------
_KIND_MAP: dict[str, str] = {
    "blank_line":    "blank_line",
    "blank_box":     "blank_box",
    "table_cell":    "table_cell",
    "tick_box":      "tick_box",
    "circle":        "circle",
    "dot":           "dot",
    # Synonyms / model variants
    "image_label":   "blank_box",
    "diagram_label": "blank_box",
    "label":         "blank_box",
    "draw_area":     "blank_box",
    "draw":          "blank_box",
    "circle_target": "circle",
    "target_circle": "circle",
    "circle_item":   "circle",
    "circled":       "circle",
    "matching_dot":  "dot",
    "match_dot":     "dot",
    "matching_point":"dot",
    "dot_match":     "dot",
    "point":         "dot",
    "empty_box":     "blank_box",
    "box":           "blank_box",
    "answer_box":    "blank_box",
    "square":        "blank_box",
    "line":          "blank_line",
    "blank":         "blank_line",
    "underline":     "blank_line",
    "checkbox":      "tick_box",
    "check_box":     "tick_box",
    "cell":          "table_cell",
}


def _norm_kind(raw: Any) -> str:
    cleaned = str(raw or "blank_line").lower().strip()
    return _KIND_MAP.get(cleaned, cleaned)


# ---------------------------------------------------------------------------
# Precision prompt
# The JSON example uses {{ }} so Python .format() treats them as literals.
# Only {ocr_context} is a real placeholder.
# ---------------------------------------------------------------------------

PAGE_ANALYSIS_PROMPT = """\
You are a universal homework and educational document extraction engine. \
Analyze the attached worksheet image and return ONE strictly valid JSON object representing its full structure and content. \
Output JSON only, with no commentary or markdown code fences.

UNIVERSAL EXTRACTION RULES:
1. Physical Reading Order & Verbatim Punctuation: Transcribe all text, numbers, punctuation, and visual elements strictly in natural reading order. When extracting inline text elements that sit between answer blanks, you MUST capture all adjacent punctuation exactly as printed on the page. If a comma separates a blank line and a word, include the comma in the text element (e.g., extract ", then" instead of "then").
2. Grounded Content: Extract only what is visibly printed or written in the image. If a field or value is missing or cropped out, use null. Never invent or hallucinate data.
3. Question Numbering & Prompts: Preserve all printed question numbers (e.g. circled numbers like "1", "2 a", "b)") in "question_no". In the "prompt" field, extract the clean problem statement WITHOUT the leading question number marker (e.g. for "1. 4 + 5 + 6 =", put "1" in "question_no" and "4 + 5 + 6 =" in "prompt"; for "2 a) Some snails live on land...", put "2 a" in "question_no" and "Some snails live on land..." in "prompt"). Never embed question numbers into mathematical expressions or calculation prompts. Construct unique IDs using the section label + printed number (e.g. "A1", "1a", "2", "3b"). If unnumbered, use sequential IDs (e.g. "A_1", "b1", "b_img1", "B_model"). If a letter/number introduces an entire section or grid (e.g. "3 Class 3 make a snail habitat in a tank.", "b) Draw one line..."), keep that overarching text at the section level ("title" / "instructions") rather than assigning it to individual grid items.
4. Context, Sub-headers & Hierarchical Grouping:
- Never drop unnumbered context, quadrant titles, helper facts, or sub-headers (including letter prefixes like "A.", "B.", "1a."). Capture unnumbered introductory text in the section/question "instructions" or "elements".
- If a section contains only a single question or matching group, place the introductory text exclusively in the question "prompt" and leave the section "instructions" null to avoid duplication.
- When multiple continuous fill-in sentences, statements, or prompt items follow a single numbered header (e.g. circled "1" followed by 3 animal grouping statements, or circled "2" followed by a list of animal names), group them together under that numbered parent question using the "sub_questions" array (e.g., parent question 1 with sub_questions 1a, 1b, 1c), or organize them under unified sections (Section 1 and Section 2) with their introductory text in section "instructions"/"title", rather than generating disconnected flat questions with null numbers.
5. Response Zones & Labeling Tasks: Identify every place intended for student input (blank lines, empty boxes, checkboxes, table cells, circle targets, matching dots) as an "answer_area" with normalized [x1, y1, x2, y2] bounding boxes on a 0-1000 scale where x1 < x2 and y1 < y2 (x1=left, y1=top, x2=right, y2=bottom). Never invert coordinates (do not output x2 < x1 or y2 < y1). If a question instructs the user/student to "Label" or mark a figure but provides no explicit printed blank lines, you MUST generate an "answer_area" (e.g., kind "blank_box" or "image_label") mapped to the bounding box of the associated figure, allowing the user a designated interactive space to interact with the image.
6. Student Work: Transcribe any student handwriting, markings, ticks, circles, or drawn lines in "student_answer". If unmarked, use null. If unreadable, use "?".
7. Multi-Column & Matching Layouts (Text & Image Grids):
- Transcribe each column, item, and visual target strictly in its physical top-to-bottom sequence as printed. Never pre-pair or re-sequence items to match opposite columns.
- For matching sections (whether text cards or image-based grids), extract each item in the left column as an independent question object (e.g., "b1", "b2", "b3") with its associated figure/text and connection dot, and extract each target item in the right column as completely separate, independent objects (e.g., "b_img1", "b_img2") with "type": "other" in their exact top-to-bottom visual order. Do not lump multi-item matching grids into a single monolithic figure.
- When extracting purely visual/image items from a matching grid, place the overarching directions in the section-level "title" or "instructions", and strictly set the "prompt" field to null for the individual image objects (both left-column and right-column items).
- If connecting lines are drawn by a student, record them in "matches" as {{"pair": [left_item, right_item], "is_example": false}}, otherwise null.
8. Figures & Diagrams (Section-Level Isolation & Visual Grid Counting): \
- If an instructional illustration or diagram sits above a set of questions and applies to the entire group (like overarching strategy models, number lines, or diagrams), extract it as a standalone item with "type": "other" (e.g. ID "B_model") before the numbered questions begin, or in the section's "figure" object. Do NOT embed it into the figure object of the first question. \
- If an image belongs specifically to an individual question item, attach it to that question's "figure" object. \
- When describing base-ten blocks, grids, or grouped objects in diagrams and figures, physically count the items in the array/grid (e.g. 2 rows of 5 = 10 units) rather than estimating or guessing the count. Populate "count" or "time_shown" only if directly depicted.
9. Header & Metadata: Extract school name (including text inside header logos, emblems, or signature stamps), homework number, subject, grade level, student name, date, and score. For signature boxes, indicate presence and whether signed.
10. Schema Compliance: Use ONLY the allowed enum values for "type" and "kind". If no specific type matches, use "other".
11. Confidence Scoring: Assign a calibrated float (0.0 to 1.0) reflecting visual clarity and legibility.
12. Warnings: Report only physical image defects (e.g. cut-off margins, heavy blur, severe glare, obscured text).

OCR TEXT AND LAYOUT REGIONS (reference hints only — image is ground truth):
{ocr_context}

Return ONLY valid JSON matching this schema:
{{
  "header": {{
    "school": null, "homework_no": null, "name": null,
    "level": null, "date": null, "score": null, "subject": null,
    "signature_box": {{"present": false, "filled": false}}
  }},
  "directions": [
    {{"label": "A", "text": "Section directions as printed."}}
  ],
  "sections": [
    {{
      "label": "A",
      "title": "Section title or prompt text",
      "instructions": null,
      "figure": {{"present": false, "description": null, "count": null, "time_shown": null}},
      "elements": [],
      "questions": [
        {{
          "id": "A1",
          "number_printed": "1",
          "type": "short_answer",
          "instructions": null,
          "prompt": "Printed question prompt text",
          "elements": [],
          "figure": {{"present": false, "description": null, "count": null, "time_shown": null}},
          "answer_areas": [{{"kind": "blank_line", "bbox": [100, 200, 300, 230]}}],
          "student_answer": null,
          "matches": null,
          "confidence": 0.95
        }}
      ]
    }}
  ],
  "footer": {{"left": null, "right": null}},
  "confidence": 0.95,
  "warnings": []
}}
"""

FIGURE_DESCRIPTION_PROMPT = """\
Describe this image from a student homework worksheet accurately and concisely.
Focus on what is visually present (e.g. "a diagram of the water cycle", \
"three coins showing 25 cents each", "an analog clock showing 3:30").
Context from surrounding text: {context}
Return JSON only: {{"description": "...", "confidence": 0.0, "count": null, "time_shown": null}}
"""


# ---------------------------------------------------------------------------
# OCR context builder
# ---------------------------------------------------------------------------

def build_ocr_context(regions: list[LayoutRegion]) -> str:
    parts = []
    for r in regions:
        texts = " | ".join(o.text for o in r.ocr_results) or "(no text)"
        bbox = [round(b) for b in r.bbox]
        parts.append(
            f"[{r.region_id}] type={r.region_type.value} bbox={bbox} text=\"{texts}\""
        )
    return "\n".join(parts) if parts else "(no regions detected)"


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json(text: str) -> dict:
    text = re.sub(r"```json\s*", "", text)
    text = re.sub(r"```\s*", "", text).strip()
    start = text.find("{")
    if start == -1:
        raise ValueError("No JSON object found in model response")
    depth = 0
    for i, ch in enumerate(text[start:], start):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
        if depth == 0:
            return json.loads(text[start: i + 1])
    raise ValueError("Unbalanced JSON braces in model response")


# ---------------------------------------------------------------------------
# Sub-parsers
# ---------------------------------------------------------------------------

_BLANK_FIELD_RE = re.compile(r"^[_.\s\-:–—]*$")


def _clean_header_field(raw: Any) -> Optional[str]:
    """Clean empty underline prompts (e.g. 'Name: ________') and extract actual text."""
    if raw is None:
        return None
    val = str(raw).strip()
    if not val:
        return None
    cleaned = re.sub(
        r"^(name|date|score|level|homework|hw|school|subject)\s*:\s*",
        "",
        val,
        flags=re.IGNORECASE,
    ).strip()
    if not cleaned or _BLANK_FIELD_RE.match(cleaned) or cleaned.lower() in ("none", "null", "n/a", "undefined"):
        return None
    return cleaned


def _parse_header(raw: Any) -> HomeworkHeader:
    if not isinstance(raw, dict):
        return HomeworkHeader()
    sb = raw.get("signature_box", {})
    return HomeworkHeader(
        school=_clean_header_field(raw.get("school")),
        homework_no=_clean_header_field(raw.get("homework_no")),
        name=_clean_header_field(raw.get("name")),
        level=_clean_header_field(raw.get("level")),
        date=_clean_header_field(raw.get("date")),
        score=_clean_header_field(raw.get("score")),
        subject=_clean_header_field(raw.get("subject")),
        signature_box=SignatureBox(
            present=bool(sb.get("present", False)) if isinstance(sb, dict) else False,
            filled=bool(sb.get("filled", False)) if isinstance(sb, dict) else False,
        ),
    )


def _parse_directions(raw: Any) -> list[Direction]:
    if not isinstance(raw, list):
        return []
    result = []
    for i in raw:
        if not isinstance(i, dict):
            continue
        lbl = str(i.get("label", "") or "").strip()
        if lbl.lower() in ("none", "null", "n/a", "undefined"):
            lbl = ""
        result.append(Direction(label=lbl, text=str(i.get("text", "") or "")))
    return result


def _parse_figure(raw: Any) -> Optional[FigureInfo]:
    if not isinstance(raw, dict):
        return None
    try:
        count = int(raw["count"]) if raw.get("count") is not None else None
    except (ValueError, TypeError):
        count = None
    return FigureInfo(
        present=bool(raw.get("present", False)),
        description=raw.get("description"),
        count=count,
        time_shown=raw.get("time_shown"),
    )


def _norm_bbox(raw: Any) -> Optional[list[float]]:
    """Validate and normalize bounding box coordinates to [x1, y1, x2, y2] where x1 < x2 and y1 < y2."""
    if not isinstance(raw, list) or len(raw) != 4:
        return None
    try:
        coords = [float(v) for v in raw]
        x1, y1, x2, y2 = coords[0], coords[1], coords[2], coords[3]
        if x1 > x2 or y1 > y2:
            logger.warning("Normalizing inverted bounding box coordinates: %s", coords)
        return [min(x1, x2), min(y1, y2), max(x1, x2), max(y1, y2)]
    except (ValueError, TypeError):
        return None


def _parse_answer_areas(raw: Any) -> list[AnswerAreaEntry]:
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        bbox = _norm_bbox(item.get("bbox"))
        result.append(AnswerAreaEntry(kind=_norm_kind(item.get("kind")), bbox=bbox))
    return result


def _parse_matches(raw: Any) -> Optional[list[list[str]]]:
    """Handle both new {pair, is_example} format and legacy [[str,str]] format."""
    if not isinstance(raw, list):
        return None
    result = []
    for item in raw:
        if isinstance(item, dict):                          # new format
            pair = item.get("pair", [])
            if isinstance(pair, list) and len(pair) == 2:
                result.append([str(pair[0]), str(pair[1])])
        elif isinstance(item, list) and len(item) == 2:    # legacy format
            result.append([str(item[0]), str(item[1])])
    return result or None


# Trailing punctuation to strip from question_no (. : ) ])
_TRAILING_PUNCT = str.maketrans("", "", ".,:;)]’”")
_HAS_DIGIT_RE = re.compile(r"\d")
# Footer subject pattern: "Subject: Maths" or "Subject:Maths"
_FOOTER_SUBJECT_RE = re.compile(r"Subject\s*:\s*(.+)", re.IGNORECASE)


def _strip_question_no(raw: Optional[str]) -> Optional[str]:
    """Strip trailing punctuation from question_no (e.g. '1.' -> '1', 'A2:' -> 'A2') and nullify sentinel strings."""
    if not raw:
        return None
    cleaned = raw.strip().rstrip(".,:;)]’”")
    if cleaned.lower() in ("none", "null", "n/a", "undefined", ""):
        return None
    return cleaned or None


def _parse_elements(raw: Any) -> list[Any]:
    """Parse raw elements list into appropriate Element objects."""
    if not isinstance(raw, list):
        return []
    result = []
    for item in raw:
        if not isinstance(item, dict):
            if isinstance(item, str) and item.strip():
                result.append(TextElement(text=item.strip()))
            continue
        etype = str(item.get("type", "text")).lower()
        if etype == "matching" or "left_item" in item or "right_item" in item:
            result.append(MatchingElement(
                left_item=item.get("left_item"),
                right_item=item.get("right_item"),
                bbox=_norm_bbox(item.get("bbox")),
            ))
        elif etype == "text" or "text" in item:
            result.append(TextElement(
                text=str(item.get("text", "")),
                bbox=_norm_bbox(item.get("bbox")),
            ))
        else:
            result.append(item)
    return result


def _strip_prompt_marker(prompt: Optional[str], question_no: Optional[str] = None) -> Optional[str]:
    """
    Strip redundant leading question list markers from prompt string.
    Ensures mathematical equations like '1. 4 + 5 + 6 =' are cleaned to '4 + 5 + 6 =',
    preventing question numbers from confusing calculation parsers and downstream LLMs.
    Preserves decimals like '1.4 + 5' (where no space follows the dot).
    """
    if not prompt or not isinstance(prompt, str):
        return prompt
    cleaned = prompt.strip()
    if not cleaned:
        return cleaned

    # 1. If question_no is given, strip specific prefix (e.g. '1.', 'Q1:', 'Problem 1:')
    if question_no:
        q_no_clean = str(question_no).strip().lstrip("Qq").rstrip(".:- ")
        if q_no_clean:
            cleaned = re.sub(
                rf"^(?:(?:[Qq]uestion|[Ee]xercise|[Pp]roblem|[Qq]|លំហាត់ទី?|សំណួរ)?\s*{re.escape(q_no_clean)}\s*[\.\)\:\-\s]+)+",
                "",
                cleaned,
                flags=re.IGNORECASE
            ).strip()

    # 2. Iteratively strip leading numbering markers:
    # '1. ', '1) ', '(1) ', '1: ', 'Q1: ', 'Question 1: ', 'Ex 1.', '1. a)', 'a) ', '(b) ', '១. ', 'លំហាត់ ១: '
    marker_pattern = re.compile(
        r"^\s*(?:"
        r"(?:[Qq]uestion|[Ee]xercise|[Ee]x|[Pp]roblem|[Qq]|លំហាត់ទី?|សំណួរ)\s*[\d១-៩]+[\.\)\:\-\s]*|"  # Q1:, Question 1:, Ex 1:, លំហាត់ ១:
        r"\(?[\d១-៩]+[\.\)]\s*\(?[a-zA-Z]\)?\s*|"  # 1. a) or 1) a)
        r"\(?[\d១-៩]+\s*[a-zA-Z]?\)\s*|"            # 1) or 1a)
        r"\(?[a-zA-Z]\)\s*|"                         # a) or (a)
        r"[\d១-៩]+\s*[\:\-]\s*(?=[a-zA-Z\u1780-\u17FF])|"
        r"[\d១-៩]+\.\s+"                             # 1. (must be followed by whitespace to preserve 1.5 decimals)
        r")\s*",
        flags=re.IGNORECASE
    )

    prev = None
    while prev != cleaned:
        prev = cleaned
        cleaned = marker_pattern.sub("", cleaned).strip()

    return cleaned or prompt


def _parse_question(q_data: dict) -> Question:
    review = (
        ReviewFlag(reason=ReviewReason.UNKNOWN, detail=str(q_data["review"]))
        if q_data.get("review") else None
    )
    # Use model's confidence exactly; None if key absent or null
    raw_conf = q_data.get("confidence")
    confidence: Optional[float] = float(raw_conf) if raw_conf is not None else None

    # Item 2: preserve raw type string so validator can report exact value
    raw_type = str(q_data.get("type", "other")).lower().strip()
    qtype = _norm_qtype(raw_type)
    if qtype == QuestionType.UNKNOWN and raw_type not in ("other", "unknown", ""):
        # Store raw value in review so validator can report it
        review = ReviewFlag(
            reason=ReviewReason.UNKNOWN,
            detail=f"unrecognised_type:{raw_type}",
        )

    # Item 3: strip trailing punctuation from question_no
    raw_no = str(q_data.get("number_printed", q_data.get("question_no", ""))).strip()
    q_no = _strip_question_no(raw_no)
    matches = _parse_matches(q_data.get("matches"))
    elements = _parse_elements(q_data.get("elements", []))

    # If matching question has matches but elements is empty, generate MatchingElements
    if qtype == QuestionType.MATCHING and matches and not elements:
        for pair in matches:
            if len(pair) == 2:
                elements.append(MatchingElement(left_item=pair[0], right_item=pair[1]))

    sub_questions = [
        _parse_question(sq) for sq in q_data.get("sub_questions", [])
        if isinstance(sq, dict)
    ]

    raw_prompt = q_data.get("prompt")
    clean_prompt = str(raw_prompt).strip() if raw_prompt is not None else None
    if clean_prompt:
        clean_prompt = _strip_prompt_marker(clean_prompt, q_no)

    return Question(
        question_no=q_no,
        question_id=str(q_data.get("id", "")).strip() or None,
        type=qtype,
        prompt=clean_prompt,
        instructions=q_data.get("instructions"),
        elements=elements,
        figure=_parse_figure(q_data.get("figure")),
        answer_areas=_parse_answer_areas(q_data.get("answer_areas", [])),
        student_answer=q_data.get("student_answer"),
        matches=matches,
        confidence=confidence,
        review=review,
        sub_questions=sub_questions,
    )


# ---------------------------------------------------------------------------
# Top-level page parser
# ---------------------------------------------------------------------------

def parse_vlm_response(data: dict, page_number: int, regions: list[LayoutRegion]) -> Page:
    """Convert the VLM JSON dict into a Page object."""
    header = _parse_header(data.get("header"))
    directions = _parse_directions(data.get("directions", []))

    # Footer
    footer_raw = data.get("footer")
    footer = None
    if isinstance(footer_raw, dict):
        footer = Footer(
            left=footer_raw.get("left"),
            right=footer_raw.get("right"),
        )

    sections: list[Section] = []
    for sec in data.get("sections", []):
        if not isinstance(sec, dict):
            continue
        questions = [_parse_question(q) for q in sec.get("questions", []) if isinstance(q, dict)]
        sec_title = sec.get("title")
        sec_instructions = sec.get("instructions")
        
        # Deduplicate single question prompt vs section instructions
        if sec_instructions and len(questions) == 1:
            if not questions[0].prompt:
                questions[0].prompt = sec_instructions
                sec_instructions = None
            elif questions[0].prompt.strip().lower() == sec_instructions.strip().lower():
                sec_instructions = None
        elif sec_instructions and questions and questions[0].prompt and questions[0].prompt.strip().lower() == sec_instructions.strip().lower():
            sec_instructions = None

        # Check if multiple matching/figure questions have copied the section title/instructions as their prompt
        overarching_texts = {
            t.strip().lower() for t in (sec_title, sec_instructions) if t and isinstance(t, str)
        }
        if overarching_texts and len(questions) > 1:
            for q in questions:
                if q.prompt and q.prompt.strip().lower() in overarching_texts:
                    q.prompt = None

        # If all questions in a matching grid have the exact same repeated prompt, lift it to section title (if unset) and nullify q.prompts
        matching_qs = [q for q in questions if q.type in (QuestionType.MATCHING, QuestionType.OTHER)]
        if len(matching_qs) > 1 and len(matching_qs) == len(questions):
            prompts = [q.prompt for q in matching_qs if q.prompt]
            if len(prompts) > 1 and len(set(p.strip().lower() for p in prompts)) == 1:
                common_prompt = prompts[0]
                if not sec_title and not sec_instructions:
                    sec_title = common_prompt
                for q in matching_qs:
                    q.prompt = None

        # Section confidence = min of question confidences (null if none rated)
        sec_q_confs = [q.confidence for q in questions if q.confidence is not None]
        sec_conf = min(sec_q_confs) if sec_q_confs else None
        sec_label = sec.get("label") or sec.get("section_id")

        # If section label was accidentally copied into the first question's question_no in a multi-item section
        if len(questions) > 1 and sec_label:
            first_q = questions[0]
            if first_q.question_no and first_q.question_no.strip().lower() == str(sec_label).strip().lower():
                other_numbers = [q.question_no for q in questions[1:] if q.question_no]
                if not other_numbers:
                    first_q.question_no = None

        sections.append(Section(
            section_id=sec_label,
            title=sec_title,
            instructions=sec_instructions,
            figure=_parse_figure(sec.get("figure")),
            elements=_parse_elements(sec.get("elements", [])),
            questions=questions,
            confidence=sec_conf,
        ))

    page = Page(
        page_number=page_number,
        header=header,
        directions=directions,
        sections=sections,
        footer=footer,
        regions=regions,
        warnings=list(data.get("warnings", [])),
    )
    # Page confidence = minimum of section confidences (or None if nothing rated)
    sec_confs = [sec.confidence for sec in sections if sec.confidence is not None]
    page.confidence = min(sec_confs) if sec_confs else None
    # Item 3: homework_no must contain a digit, else null
    if header and header.homework_no:
        if not _HAS_DIGIT_RE.search(header.homework_no):
            logger.debug("homework_no %r has no digit — nulled", header.homework_no)
            header.homework_no = None

    # Item 3: subject fallback from footer text
    if header and not header.subject and footer:
        for text in (footer.left or "", footer.right or ""):
            m = _FOOTER_SUBJECT_RE.search(text)
            if m:
                header.subject = m.group(1).strip()
                logger.debug("Subject inferred from footer: %r", header.subject)
                break

    # Title fallback: use school name, or first banner direction (where label is empty)
    doc_title = (header.school if header and header.school else None)
    if not doc_title and directions:
        for d in directions:
            # Only use banner-style directions without a section letter (e.g. "Grouping animals")
            if not d.label and d.text and len(d.text) < 120:
                doc_title = d.text
                break

    page._meta = {
        "title": doc_title,
        "subject": header.subject if header else None,
        "grade_level": header.level if header else None,
        "language": ["English"],
    }
    return page


def make_error_page(page_number: int, regions: list[LayoutRegion], reason: str) -> Page:
    """Return a stub Page when the VLM call or JSON parse fails."""
    page = Page(
        page_number=page_number,
        regions=regions,
        confidence=0.1,
        warnings=[reason],
    )
    page.sections = [Section(
        section_id="error",
        questions=[Question(
            question_no="?",
            type=QuestionType.UNKNOWN,
            prompt=reason,
            confidence=0.1,
            review=ReviewFlag(reason=ReviewReason.LOW_VLM_CONFIDENCE, detail=reason),
        )],
    )]
    page._meta = {}
    return page
