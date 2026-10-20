"""
File: orchestrator/app/services/visuals/__init__.py
Description: Package initializer for deterministic SVG VisualSpec generators.
             Exports schema types, the 6 visual builders, and the visual leak checker.
             Implements Architecture v2.1 Section 8.
"""

from app.services.visuals.schema import (
    VisualType,
    VisualMode,
    VisualSpec,
    VisualHighlight,
)
from app.services.visuals.builders.ten_frame import build_ten_frame
from app.services.visuals.builders.number_line import build_number_line
from app.services.visuals.builders.base_ten_blocks import build_base_ten_blocks
from app.services.visuals.builders.array_grid import build_array_grid
from app.services.visuals.builders.fraction_bar import build_fraction_bar
from app.services.visuals.builders.bar_model import build_bar_model
from app.services.visuals.leak_checker import check_visual_spec_leak

__all__ = [
    "VisualType",
    "VisualMode",
    "VisualSpec",
    "VisualHighlight",
    "build_ten_frame",
    "build_number_line",
    "build_base_ten_blocks",
    "build_array_grid",
    "build_fraction_bar",
    "build_bar_model",
    "check_visual_spec_leak",
]
