# Phase 1D Implementation Plan: Unified Gap Accounting & PostgreSQL Schema

> **Target Spec:** [`docs/ReanMore_Architecture_v2.1.md`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/docs/ReanMore_Architecture_v2.1.md) (Section 11, Section 11.1, Section 11.2, Section 11.3)  
> **Status:** COMPLETED & VERIFIED ✅ (All 8 gap tests passed, 249 socratic tests passed)  
> **Prerequisites:** PostgreSQL 16 Alpine connection available.

---

## 1. Objectives & Scope

Phase 1D establishes the **Unified Gap Accounting** architecture, aggregating content gaps, learner struggles, and system reliability events into a single PostgreSQL ledger with weekly actionable digests:
1. **PostgreSQL Schema Migration:** Create `gap_events` table and the aggregated `gap_summary` view.
2. **Implement Telemetry Event Dispatcher:** Non-blocking async event logging across all orchestrator nodes.
3. **Capture Complete 3-Tier Taxonomy:** `content` gaps, `learner` gaps, and `system` events.
4. **Automate Weekly Admin Audit Digest:** Standalone Python CLI script (`scripts/generate_admin_digest.py`) producing Monday morning summaries.

---

## 2. Current State vs Target Architecture

| Component | Current Implementation | Target Specification | Status | Evidence (`file:line`) |
| :--- | :--- | :--- | :--- | :--- |
| **Gap Event Storage** | Separate `curriculum_gap_reports` table & general logs | Unified `gap_events` table covering content, learner, & system | `PARTIAL` | [`database.py:L20-105`](file:///e:/Competition/Khmer%20Enterprise/Science_chatbot/backend/orchestrator/app/infrastructure/database.py#L20-L105) |
| **Summary View** | Ad-hoc SQL queries | `gap_summary` database view with priority score formula | `MISSING` | Target: `init_db()` migration |
| **Event Taxonomy** | Fragmented string codes | Standardized taxonomy (`NO_SKILL_MATCH`, `STEP_ERROR_STREAK`, `LEAK_BLOCKED`, etc.) | `PARTIAL` | `backend/orchestrator/app/` |
| **Admin Digest CLI** | None | `scripts/generate_admin_digest.py` generating weekly markdown digests | `MISSING` | `scripts/` |

---

## 3. Step-by-Step Implementation Steps

### Step 1D.1: Database Migration (`gap_events` & `gap_summary`)

In `backend/orchestrator/app/infrastructure/database.py`:
- Add ORM model:
  ```python
  class GapEvent(Base):
      __tablename__ = "gap_events"

      id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
      timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, index=True)
      session_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("session_logs.session_id", ondelete="SET NULL"), nullable=True, index=True)
      user_id: Mapped[Optional[str]] = mapped_column(String(100), ForeignKey("student_profiles.user_id", ondelete="SET NULL"), nullable=True, index=True)
      grade_level: Mapped[str] = mapped_column(String(20))
      domain: Mapped[str] = mapped_column(String(50), default="math")
      gap_type: Mapped[str] = mapped_column(String(20), index=True) # "content", "learner", "system"
      event_code: Mapped[str] = mapped_column(String(50), index=True)
      details: Mapped[Dict[str, Any]] = mapped_column(JSON)
      severity: Mapped[str] = mapped_column(String(20)) # "info", "warning", "critical"
      resolved: Mapped[bool] = mapped_column(Boolean, default=False)
      reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
      reviewed_by: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
  ```
- In `init_db()`, execute migration script creating the `gap_summary` view:
  ```sql
  CREATE OR REPLACE VIEW gap_summary AS
  SELECT 
      gap_type,
      event_code,
      grade_level,
      domain,
      COUNT(*) AS occurrence_count,
      COUNT(DISTINCT user_id) AS impacted_students,
      MAX(timestamp) AS last_occurred_at,
      SUM(CASE WHEN resolved = FALSE THEN 1 ELSE 0 END) AS unreviewed_count
  FROM gap_events
  GROUP BY gap_type, event_code, grade_level, domain;
  ```

### Step 1D.2: Asynchronous Event Dispatcher (`gap_recorder.py`)

Create `backend/orchestrator/app/services/telemetry/gap_recorder.py`:
```python
async def record_gap_event(
    gap_type: Literal["content", "learner", "system"],
    event_code: str,
    grade_level: str,
    details: Dict[str, Any],
    severity: Literal["info", "warning", "critical"] = "info",
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    domain: str = "math"
) -> None:
    # Non-blocking async insert to PostgreSQL
```

### Step 1D.3: Instrument Orchestrator Telemetry Points

Hook event dispatchers into the active pipeline:
1. **Content Gaps:**
   - In `skills/registry.py`: emit `NO_SKILL_MATCH` when a math inquiry does not match any template.
   - In `parse_verifier.py`: emit `PARSE_UNCONFIRMED` if child clicks "No" on clarification.
2. **Learner Gaps:**
   - In `graph.py`: emit `STEP_ERROR_STREAK` upon 3 consecutive incorrect attempts.
   - In `hint_engine.py`: emit `HINT_ESCALATION` when student requests Tier 3 hint.
   - In `reveal_and_continue.py`: emit `REVEAL_TRIGGERED`.
3. **System Gaps:**
   - In `manager.py`: emit `LLM_TIMEOUT` when first token exceeds 6.0 s deadline.
   - In `leak_guard.py`: emit `LEAK_BLOCKED` when an answer disclosure is quarantined.
   - In `quota_guard.py`: emit `QUOTA_EXHAUSTED` when daily cap is hit.

### Step 1D.4: Weekly Admin Audit Digest (`scripts/generate_admin_digest.py`)

Create standalone CLI script:
- Queries `gap_events` over the past 7 days.
- Ranks top content gaps (skills most frequently missing from curriculum).
- Ranks top learner struggle topics (concepts triggering the highest Tier 3 hint escalations).
- Calculates system reliability SLA: $\frac{\text{Successful Turns}}{\text{Total Turns}} \times 100\%$.
- Emits formatted GitHub-style Markdown report to `docs/digests/digest_YYYY_MM_DD.md` and prints summary to console.

---

## 4. Verification & Testing Protocol

Execute from workspace root:

```powershell
# 1. Test database ORM creation and gap recording
& .venv\Scripts\python.exe -m pytest backend/testing/unit/test_gap_recorder.py -v

# 2. Test weekly digest CLI generation
& .venv\Scripts\python.exe scripts/generate_admin_digest.py --days 7 --dry-run
```

### Exit Criteria
- [x] `gap_events` table and `gap_summary` view create cleanly on startup.
- [x] Telemetry events log asynchronously without degrading request latency (< 5 ms overhead).
- [x] `generate_admin_digest.py` produces an actionable markdown report with prioritized rankings.
