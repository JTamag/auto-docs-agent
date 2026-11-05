> **PR Link:** [JTamag/auto-docs-agent-sandbox#1](https://github.com/JTamag/auto-docs-agent-sandbox/pull/1)  
> **Status:** Draft (Needs Human Review)  
> **Author:** @JTamag  
> **Merged:** True (2026-11-03T21:59:01Z)  
> **Generated:** 2026-11-05 00:41:15 UTC  

---

# [Technical Doc]: feat: add learner progress tracking endpoint and calculation

## Overview & Purpose
This change introduces module completion progress tracking for learners, giving learners and learning coaches direct visibility into module completion rates and streak data within the portal. It implements a dedicated progress calculation module and exposes a new authenticated GET endpoint.

## What Changed
- Created a new module `progress.py` containing progress calculation logic and data retrieval functions.
- Added a new authenticated API endpoint `GET /learners/{learner_id}/progress` to `app.py`.
- Implemented error handling to return a `404 Not Found` response if a requested learner ID does not exist.

## Implementation Details
- **`progress.py`**:
  - `PROGRESS_DATA`: In-memory dictionary mapping learner IDs to tracking metrics (`modules_completed`, `current_streak_days`, `last_active`).
  - `calculate_completion_percentage(completed: int, total: int = 24) -> float`: Computes the rounded percentage of completed modules against a default total of 24. Includes zero-division protection (`total <= 0`).
  - `get_learner_progress(learner_id: int) -> dict`: Retrieves progress data for a given learner, calculating the completion percentage and returning a structured payload including streak days and last active date. If the learner ID is absent from `PROGRESS_DATA`, it falls back to a default "not started" state.
    ```python
    def get_learner_progress(learner_id: int) -> dict:
        data = PROGRESS_DATA.get(learner_id)
        if not data:
            return {"modules_completed": 0, "completion_pct": 0.0, "status": "not_started"}
        
        pct = calculate_completion_percentage(data["modules_completed"])
        return {
            "learner_id": learner_id,
            "modules_completed": data["modules_completed"],
            "completion_percentage": pct,
            "streak_days": data["current_streak_days"],
            "last_active": data["last_active"]
        }
    ```

- **`app.py`**:
  - Added the `GET /learners/{learner_id}/progress` route protected by the `verify_token` dependency.
  - Validates that the requested `learner_id` exists in the global `LEARNERS` collection before invoking `get_learner_progress()`, raising a `404 HTTPException` if validation fails.

## Maintenance & Operational Notes
- **Authentication**: The new progress endpoint relies on the existing `verify_token` dependency and inherits standard authentication requirements.
- **Data Source**: Progress and learner validation currently rely on in-memory data stores (`PROGRESS_DATA` and `LEARNERS`). When migrating to a persistent database layer, these lookups will need to be refactored to asynchronous DB queries.
- **Default Total Modules**: The completion calculation hardcodes a default total of `24` modules. If curriculum lengths become dynamic per learner or module track, `calculate_completion_percentage` should be updated to accept a dynamic total parameter.