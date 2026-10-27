"""
Pydantic schemas for the Homework JSON output.
This is the single contract that every pipeline stage writes to,
and that the downstream chatbot reads from.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------

class QuestionType(str, Enum):
    MULTIPLE_CHOICE = "multiple_choice"
    FILL_BLANK = "fill_blank"
    SHORT_ANSWER = "short_answer"
    LONG_ANSWER = "long_answer"
    MATCHING = "matching"
    VISUAL_COUNTING = "visual_counting"
    TRUE_FALSE = "true_false"
    CIRCLE = "circle"
    TICK = "tick"
    TABLE = "table"
    ORDERING = "ordering"
    DRAW = "draw"
    LABEL_DIAGRAM = "label_diagram"
    MATH_EQUATION = "math_equation"
    WORD_BANK = "word_bank"
    OTHER = "other"
    UNKNOWN = "unknown"


class ElementType(str, Enum):
    TEXT = "text"
    FIGURE = "figure"
    TABLE = "table"
    DIAGRAM = "diagram"
    GRAPH = "graph"
    ANSWER_AREA = "answer_area"
    CHECKBOX = "checkbox"
    MATCHING = "matching"
    STUDENT_ANSWER = "student_answer"
    MATH = "math"
    BLANK_LINE = "blank_line"
    HEADER = "header"
    INSTRUCTION = "instruction"
    UNKNOWN = "unknown"


class AnswerSubtype(str, Enum):
    BLANK_LINE = "blank_line"
    BLANK_BOX = "blank_box"
    CHECKBOX = "checkbox"
    CIRCLE = "circle"
    TICK = "tick"
    TABLE_CELL = "table_cell"
    DRAW_AREA = "draw_area"


class RegionType(str, Enum):
    HEADER = "header"
    INSTRUCTION = "instruction"
    SECTION = "section"
    QUESTION = "question"
    SUB_QUESTION = "sub_question"
    TEXT_BLOCK = "text_block"
    TABLE = "table"
    FIGURE = "figure"
    DIAGRAM = "diagram"
    GRAPH = "graph"
    BLANK_LINE = "blank_line"
    ANSWER_BOX = "answer_box"
    CHECKBOX = "checkbox"
    MATCHING_LINE = "matching_line"
    HANDWRITTEN = "handwritten"
    UNKNOWN = "unknown"


class ReviewReason(str, Enum):
    HANDWRITING_UNCLEAR = "handwriting_unclear"
    LOW_OCR_CONFIDENCE = "low_ocr_confidence"
    LOW_VLM_CONFIDENCE = "low_vlm_confidence"
    MATH_UNRECOGNIZED = "math_unrecognized"
    FIGURE_UNRECOGNIZED = "figure_unrecognized"
    MATCHING_UNCLEAR = "matching_unclear"
    LAYOUT_AMBIGUOUS = "layout_ambiguous"
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Low-level building blocks
# ---------------------------------------------------------------------------

BBox = list[float]  # [x, y, w, h]  or  [x1, y1, x2, y2] — normalised later


class ReviewFlag(BaseModel):
    status: str = "needs_review"
    reason: ReviewReason = ReviewReason.UNKNOWN
    detail: Optional[str] = None


class OCRResult(BaseModel):
    """Raw output from the OCR engine for a single text span."""
    text: str
    bbox: BBox
    confidence: float
    page_number: int = 1
    region_id: Optional[str] = None


class LayoutRegion(BaseModel):
    """A region detected by the layout engine (PP-Structure)."""
    region_id: str
    region_type: RegionType
    bbox: BBox
    page_number: int = 1
    ocr_results: list[OCRResult] = Field(default_factory=list)
    image_reference: Optional[str] = Field(default=None, exclude=True)   # base64 crop — internal only, not serialised
    confidence: float = 1.0
    review: Optional[ReviewFlag] = None
    raw_layout_label: Optional[str] = None  # original PP-Structure label


# ---------------------------------------------------------------------------
# Question elements
# ---------------------------------------------------------------------------

class TextElement(BaseModel):
    type: ElementType = ElementType.TEXT
    text: str
    bbox: Optional[BBox] = None
    confidence: float = 1.0
    review: Optional[ReviewFlag] = None


class FigureElement(BaseModel):
    type: ElementType = ElementType.FIGURE
    bbox: Optional[BBox] = None
    image_reference: Optional[str] = None
    description: Optional[str] = None
    confidence: float = 0.0
    review: Optional[ReviewFlag] = None


class AnswerAreaElement(BaseModel):
    type: ElementType = ElementType.ANSWER_AREA
    subtype: AnswerSubtype = AnswerSubtype.BLANK_LINE
    bbox: Optional[BBox] = None
    label: Optional[str] = None       # e.g. "A", "B", "C" for choices
    confidence: float = 1.0
    review: Optional[ReviewFlag] = None


class CheckboxElement(BaseModel):
    type: ElementType = ElementType.CHECKBOX
    label: Optional[str] = None
    checked: Optional[bool] = None
    bbox: Optional[BBox] = None
    confidence: float = 0.0
    review: Optional[ReviewFlag] = None


class MatchingElement(BaseModel):
    type: ElementType = ElementType.MATCHING
    left_item: Optional[str] = None
    right_item: Optional[str] = None
    connection: Optional[dict[str, Any]] = None
    bbox: Optional[BBox] = None
    confidence: float = 0.0
    review: Optional[ReviewFlag] = None


class StudentAnswerElement(BaseModel):
    type: ElementType = ElementType.STUDENT_ANSWER
    text: Optional[str] = None
    bbox: Optional[BBox] = None
    is_handwritten: bool = True
    confidence: float = 0.0
    review: Optional[ReviewFlag] = None


class MathElement(BaseModel):
    type: ElementType = ElementType.MATH
    latex: Optional[str] = None
    plain_text: Optional[str] = None
    bbox: Optional[BBox] = None
    image_reference: Optional[str] = None
    confidence: float = 0.0
    review: Optional[ReviewFlag] = None


class TableElement(BaseModel):
    type: ElementType = ElementType.TABLE
    rows: list[list[Any]] = Field(default_factory=list)
    bbox: Optional[BBox] = None
    image_reference: Optional[str] = None
    confidence: float = 0.0
    review: Optional[ReviewFlag] = None


# Union type for question elements
QuestionElement = (
    TextElement
    | FigureElement
    | AnswerAreaElement
    | CheckboxElement
    | MatchingElement
    | StudentAnswerElement
    | MathElement
    | TableElement
)


# ---------------------------------------------------------------------------
# Question / Section / Page
# ---------------------------------------------------------------------------

class Question(BaseModel):
    question_no: Optional[str] = None    # Preserve exactly as printed
    question_id: Optional[str] = None   # e.g. "A1", "B4" from precision prompt
    type: QuestionType = QuestionType.UNKNOWN
    prompt: Optional[str] = None
    instructions: Optional[str] = None
    elements: list[Any] = Field(default_factory=list)   # QuestionElement list
    figure: Optional[FigureInfo] = None
    answer_areas: list[AnswerAreaEntry] = Field(default_factory=list)
    student_answer: Optional[Any] = None
    matches: Optional[list[list[str]]] = None
    confidence: Optional[float] = None   # None = model did not emit a value
    review: Optional[ReviewFlag] = None
    sub_questions: list["Question"] = Field(default_factory=list)


class Section(BaseModel):
    section_id: Optional[str] = None    # "A", "B", "I", "II", etc.
    title: Optional[str] = None
    instructions: Optional[str] = None
    figure: Optional[FigureInfo] = None
    elements: list[Any] = Field(default_factory=list)
    questions: list[Question] = Field(default_factory=list)
    confidence: Optional[float] = None   # computed as min of question confidences


class Page(BaseModel):
    page_number: int
    width: Optional[int] = None
    height: Optional[int] = None
    header: Optional[HomeworkHeader] = None
    directions: list[Direction] = Field(default_factory=list)
    sections: list[Section] = Field(default_factory=list)
    footer: Optional[Footer] = None
    # Raw detected regions (preserved for debugging/VLM reference)
    regions: list[LayoutRegion] = Field(default_factory=list)
    confidence: Optional[float] = None   # None until VLM sets it
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Top-level document
# ---------------------------------------------------------------------------

class DocumentMeta(BaseModel):
    title: Optional[str] = None
    language: list[str] = Field(default_factory=lambda: ["English"])
    pages: int = 1
    subject: Optional[str] = None
    grade_level: Optional[str] = None


class ValidationResult(BaseModel):
    passed: bool = True
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


class HomeworkResponse(BaseModel):
    """Final API response schema."""
    status: str = "success"
    document: DocumentMeta
    pages: list[Page]
    confidence: Optional[float] = None
    warnings: list[str] = Field(default_factory=list)
    validation: Optional[ValidationResult] = None
    processing_time_seconds: Optional[float] = None
    stage_timers: Optional[dict[str, float]] = None   # preprocess/layout_ocr/vlm/validation in seconds
    bbox_unit: str = "normalized_1000"  # changed to "px" after pixel conversion
    pipeline_version: str = "1.0.0"



# ---------------------------------------------------------------------------
# New rich extraction models (matching the precision prompt schema)
# ---------------------------------------------------------------------------

class SignatureBox(BaseModel):
    present: bool = False
    filled: bool = False


class HomeworkHeader(BaseModel):
    school: Optional[str] = None
    homework_no: Optional[str] = None
    name: Optional[str] = None
    level: Optional[str] = None
    date: Optional[str] = None
    score: Optional[str] = None
    subject: Optional[str] = None
    signature_box: SignatureBox = Field(default_factory=SignatureBox)


class Footer(BaseModel):
    left: Optional[str] = None
    right: Optional[str] = None


class Direction(BaseModel):
    label: str
    text: str


class FigureInfo(BaseModel):
    present: bool = False
    description: Optional[str] = None
    count: Optional[int] = None
    time_shown: Optional[str] = None


# Allowed kind and type values (enforced by validator)
QUESTION_KINDS = frozenset({
    "blank_line", "blank_box", "table_cell", "tick_box", "circle", "dot",
})

ALLOWED_QUESTION_TYPES = frozenset({
    "fill_blank", "equation", "match", "circle", "tick", "table", "draw",
    "order", "multiple_choice", "short_answer", "other",
    # aliases that map cleanly
    "math_equation", "matching", "ordering",
})


class AnswerAreaEntry(BaseModel):
    kind: str = "blank_line"   # expected: blank_line|blank_box|table_cell|tick_box|circle|dot
    bbox: Optional[BBox] = None   # [x1,y1,x2,y2] on 0-1000 scale (int); pixel after conversion
    # Note: unknown kind values are stored as-is and flagged by the Validator


# Rebuild for forward refs
Question.model_rebuild()
