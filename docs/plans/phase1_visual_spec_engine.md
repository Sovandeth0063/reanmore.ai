# Phase 1B Implementation Plan: Deterministic VisualSpec Engine & Pure SVG Renderer

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](../../docs/ReanMore_Architecture_v2.1.md) (Section 8, Section 8.1, Section 8.2)  
> **Status:** COMPLETED & VERIFIED ✅  
> **Prerequisites:** Phase 1A complete (`StepTemplate` models defined).

---

## 1. Objectives & Scope

Phase 1B implements the deterministic visual explanation engine that generates structured JSON specs on the backend and renders them as accessible, pure SVG diagrams on the React frontend:
1. **Deterministic Backend VisualSpec Generator:** Python builders generating JSON specs for 6 elementary visual models.
2. **Answer-Safe Mode Isolation:** Enforce `current`, `example`, and `reveal` modes with strict parameter gating.
3. **Deterministic Visual Leak Check:** Pre-serialization scan ensuring no SVG parameter, counter quantity, or label discloses an unsolved target.
4. **Frontend Pure SVG `<VisualRenderer />`:** React component rendering SVG diagrams with kid-friendly colors, subtle micro-animations, and ARIA labels.

---

## 2. Current State vs Target Architecture

| Component | Current Implementation | Target Specification | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| **Visual Generation** | LLM text output / emoji strings | Deterministic Python CAS builders | `CONFLICTS` | [`card_schema.py:L74-75`](../../backend/orchestrator/app/services/socratic/card_schema.py#L74-L75) |
| **Visual Schema** | Untyped `visual_data: Optional[Dict]` | Strict `VisualSpec` schema (v1) with typed models | `PARTIAL` | [`card_schema.py:L60-63`](../../backend/orchestrator/app/services/socratic/card_schema.py#L60-L63) |
| **6 SVG Models** | 3 ad-hoc prototypes (`NumberLine`, `PlaceValue`, `ObjectGroups`) | 6 unified SVG models (`ten_frame`, `number_line`, `base_ten_blocks`, `array_grid`, `fraction_bar`, `bar_model`) | `PARTIAL` | `frontend/src/components/widgets/` |
| **Visual Leak Scan** | None | Multi-point parameter and label scan | `MISSING` | Target: `visual_leak_check.py` |
| **Frontend Renderer** | Fragmented widget loading | Unified `<VisualRenderer spec={...} />` | `MISSING` | `frontend/src/components/` |

---

## 3. Step-by-Step Implementation Steps

### Step 1B.1: Backend `VisualSpec` Schema & Builders (`orchestrator/app/services/socratic/visual/`)

Create `schema.py` and dedicated builder modules:

```python
class VisualType(str, Enum):
    TEN_FRAME = "ten_frame"
    NUMBER_LINE = "number_line"
    BASE_TEN_BLOCKS = "base_ten_blocks"
    ARRAY_GRID = "array_grid"
    FRACTION_BAR = "fraction_bar"
    BAR_MODEL = "bar_model"

class VisualMode(str, Enum):
    CURRENT = "current"    # Given quantities only; never the unknown target
    EXAMPLE = "example"    # Parallel worked problem with strictly distinct numbers
    REVEAL = "reveal"      # Completed solution diagram (only after 3 failed tries)

class VisualSpec(BaseModel):
    schema_version: int = 1
    type: VisualType
    mode: VisualMode
    answer_safe: bool = True
    params: Dict[str, Any]
    highlights: List[Dict[str, Any]] = Field(default_factory=list)
    labels: List[str] = Field(default_factory=list)
    alt_text: str
```

### Step 1B.2: Implement the 6 Python Visual Builders

1. **`build_ten_frame(a, b, mode)`**: 2x5 grid matrices showing full tens and leftover ones, with transfer arrows.
2. **`build_number_line(start, step, jumps, mode)`**: Clean horizontal line with labeled intervals and arc hops. In `current` mode, the landing mark is omitted.
3. **`build_base_ten_blocks(tens, ones, regroup=False, mode)`**: Grid of hundreds flats, tens rods, and unit blocks with regrouping badges.
4. **`build_array_grid(rows, cols, mode)`**: Grid of items/dots with group boundary brackets for multiplication.
5. **`build_fraction_bar(num, den, equiv_den=None, mode)`**: Partitioned rectangle with shaded numerator slices.
6. **`build_bar_model(whole, parts, unknown_part=None, mode)`**: Tape diagram comparing parts to whole. The unknown box renders as `?`.

### Step 1B.3: Deterministic Visual Leak Check (`visual_leak_check.py`)

Execute prior to embedding `VisualSpec` into `StepWidgetPayload`:
1. If `mode != "reveal"`:
   - Check all scalar values in `params` (e.g. `filled`, `count`, `jumps`, `sum`).
   - If any value equals an active or future step target, raise `VisualLeakException` and fall back to safe empty scaffolding.
2. If `mode == "example"`:
   - Verify zero intersection between example parameters and the student's problem numbers.
3. Send all strings in `labels` and `alt_text` through Leak Guard v2.

### Step 1B.4: Frontend Pure SVG `<VisualRenderer />` (`frontend/src/components/visual/`)

Build modular React SVG components:
- `VisualRenderer.tsx`: Dispatches to specific SVG renderer based on `spec.type`.
- `TenFrameSVG.tsx`: Renders ten-frame cells and animated circular counters.
- `NumberLineSVG.tsx`: Renders coordinate axis, tick marks, and quadratic Bézier arc paths (`<path d="M... Q..." />`).
- `BaseTenBlocksSVG.tsx`: Renders isometric or 2D blocks with distinct colors for hundreds (emerald), tens (amber), ones (indigo).
- `ArrayGridSVG.tsx`: Renders dot arrays with interactive hover focus.
- `FractionBarSVG.tsx`: Renders segmented bars with fraction labels.
- `BarModelSVG.tsx`: Renders Singapore-math style part-whole tape diagrams.

---

## 4. Verification & Testing Protocol

Execute from `backend/`:

```powershell
# 1. Run backend VisualSpec builder and leak check tests
& ..\.venv\Scripts\python.exe -m pytest testing/unit/socratic/test_visual_spec.py -v
```

Execute frontend build verification:
```powershell
cd frontend
npm run build
```

### Exit Criteria
- [ ] 6 visual builders generate schema-compliant `VisualSpec` dictionaries.
- [ ] Visual leak check blocks any spec in `current` mode that displays the target answer.
- [ ] In `example` mode, visual specs use completely distinct numbers.
- [ ] Frontend `<VisualRenderer />` renders cleanly with zero console errors or hydration mismatches.
