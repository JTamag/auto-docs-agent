> **PR Link:** [JTamag/auto-docs-agent-sandbox#5](https://github.com/JTamag/auto-docs-agent-sandbox/pull/5)  
> **Status:** Draft (Needs Human Review)  
> **Author:** @JTamag  
> **Merged:** True (2026-11-03T22:01:15Z)  
> **Generated:** 2026-11-05 00:50:39 UTC  

---

# [Technical Doc]: refactor: Add in-memory TTL caching for course catalog

## Overview & Purpose
This change introduces an in-memory TTL (Time-To-Live) caching mechanism to the course catalog module to reduce redundant simulated database fetches. It uses a local dictionary cache with a 5-minute expiration window, chosen to balance data freshness with performance for a rarely changing catalog under single-instance portal traffic.

## What Changed
- Added a local in-memory cache structure to store course catalog data alongside a timestamp.
- Implemented a 5-minute TTL (`CACHE_TTL_SECONDS = 300`) expiration check within the course retrieval logic.
- Added a `force_refresh` boolean parameter to `get_courses()` to allow bypassing the cache when necessary.

## Implementation Details
The caching mechanism is implemented entirely within `courses.py` using standard library primitives (`time`). 

- **Data Structures**:
  - `COURSES_DB`: Static list containing course records.
  - `_CACHE`: A dictionary tracking the cached data list and the epoch timestamp of the last fetch.
- **Functions**:
  - `get_courses(force_refresh: bool = False) -> list[dict]`: Checks if the current time minus the cache timestamp is within the 300-second TTL. If valid and `force_refresh` is false, it returns the cached list. Otherwise, it updates the cache with a fresh copy of `COURSES_DB` and returns it.

```python
_CACHE = {"timestamp": 0, "data": []}
CACHE_TTL_SECONDS = 300  # 5 minutes

def get_courses(force_refresh: bool = False) -> list[dict]:
    """Retrieve courses catalog with local TTL caching."""
    now = time.time()
    if not force_refresh and _CACHE["data"] and (now - _CACHE["timestamp"] < CACHE_TTL_SECONDS):
        return _CACHE["data"]

    # Simulating DB fetch
    _CACHE["data"] = list(COURSES_DB)
    _CACHE["timestamp"] = now
    return _CACHE["data"]
```

## Maintenance & Operational Notes
- **Scope Limitations**: The cache is stored entirely in local process memory (`_CACHE` dictionary). If the application is scaled horizontally across multiple instances or serverless functions, cache states will not be synchronized globally.
- **Forcing Refreshes**: Callers that require immediate consistency (e.g., immediately following an administrative update to the catalog) should invoke `get_courses(force_refresh=True)`.