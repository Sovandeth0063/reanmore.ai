"""
File: orchestrator/app/services/visuals/schema.py
Description: Pydantic schemas for deterministic SVG Visual Models.
             Implements Architecture v2.1 Section 8.1.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ConfigDict


class VisualType(str, Enum):
    TEN_FRAME = "ten_frame"
    NUMBER_LINE = "number_line"
    BASE_TEN_BLOCKS = "base_ten_blocks"
    ARRAY_GRID = "array_grid"
    FRACTION_BAR = "fraction_bar"
    BAR_MODEL = "bar_model"


class VisualMode(str, Enum):
    CURRENT = "current"    # Given problem quantities only; unknown target omitted
    EXAMPLE = "example"    # Parallel worked problem with strictly disjoint numbers
    REVEAL = "reveal"      # Completed solution diagram (only after 3 failed tries)


class VisualHighlight(BaseModel):
    model_config = ConfigDict(extra="allow")

    type: Optional[str] = None
    from_frame: Optional[int] = None
    to_frame: Optional[int] = None
    move: Optional[int] = None
    indices: List[int] = Field(default_factory=list)
    color: Optional[str] = None
    amount: Optional[int] = None


class VisualSpec(BaseModel):
    """
    Standardized visual representation payload for SVG rendering on web clients.
    Guaranteed deterministic and answer-safe.
    """
    model_config = ConfigDict(extra="allow", populate_by_name=True)

    schema_version: int = Field(default=1, description="VisualSpec schema version")
    type: VisualType = Field(..., description="Visual manipulative type")
    mode: VisualMode = Field(default=VisualMode.CURRENT, description="Visual rendering mode (current, example, reveal)")
    answer_safe: bool = Field(default=True, description="Enforced True for current/example; only False in reveal")
    params: Dict[str, Any] = Field(default_factory=dict, description="Model-specific numerical configuration")
    highlights: List[VisualHighlight] = Field(default_factory=list, description="Visual highlights and animations")
    labels: List[str] = Field(default_factory=list, description="Descriptive labels for visual components")
    alt_text: str = Field(..., description="Screen-reader accessible ARIA description")
