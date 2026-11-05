# Auto Docs Agent

An agentic pipeline that generates developer and end-user documentation from GitHub Pull Request context. Internship project for Brave Generation Academy.

Status: Functional MVP operational (ingestion, context gate, Gemini generation, output writer, and run logging implemented).

## Overview

When a team builds a feature, most of the reasoning behind it ends up in the PR: the description, the diff, the review comments. Once the PR is merged that context gets buried, and the documentation is either written by hand later or never written at all.

This project explores whether a PR can be turned into useful documentation automatically, for two different audiences:

*   **Technical documentation** for developers: architecture, implementation details and technical decisions that matter when maintaining the code.
*   **Non-technical documentation** for end users (Learners, Learning Coaches, Course Managers): what changed and what it means for them, in plain language.

The first version only covers the technical documentation. End-user docs come later (see the roadmap).

## MVP Scope

The MVP is deliberately small. It is the minimum that already delivers value:

1.  Take a single merged PR.
2.  Read its title, description, diff and comments (`ingest.py`).
3.  Check if context is sufficient; ask targeted questions if not (`context_check.py`).
4.  Generate technical documentation while stripping sensitive details (`generate.py`).
5.  Save it as a draft markdown file in `docs/generated/pr-<number>.md`.
6.  Append an event record to `docs/generated/run_log.jsonl` to track success criteria.
7.  Require human review before anything is published.

If a PR does not contain enough information to document it properly, the agent asks for more context instead of filling the gaps with guesses.

## Architecture

MVP flow:

```text
GitHub PR (merged)
   |
   v
Ingestion (ingest.py): title, description, diff, comments (filters lockfile noise)
   |
   v
Context Gate (context_check.py): Enough context to document?
   |-- no  --> writes questions for the author to docs/generated/pr-<number>-clarification.md
   |
   v (yes)
Technical Doc Generation (generate.py): Gemini API with strict sensitive info guardrails
   |
   v
Draft Output (main.py): docs/generated/pr-<number>.md (marked as needing review)
   |
   v
Run Log (main.py): docs/generated/run_log.jsonl (records context check pass & reviewer corrections)
   |
   v
Human review --> publish
```

Planned after the MVP:

*   Issues and commit messages as additional context
*   A separate analysis stage ahead of generation
*   End-user documentation generation
*   Context store / audit log of features and events
*   Weekly or bi-weekly summaries

## How to Run the MVP

### Prerequisites
1. Clone the repository and install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Configure credentials:
   ```bash
   cp .env.example .env
   ```
   Add your `GITHUB_TOKEN` and `GEMINI_API_KEY` to `.env` (this file is git-ignored and never committed).

### CLI Usage
Run the end-to-end pipeline against any PR:

```bash
cd auto-docs-agent

# Run against PR #1 (Golden PR with complete description and diff)
python main.py --pr 1

# Run against PR #2 (Low-context PR - automatically triggers the Context Gate)
python main.py --pr 2

# Run against PR #4 (Sensitive credential trap - tests secret omission)
python main.py --pr 4
```

To target a different repository:
```bash
python main.py --repo owner/repo-name --pr 12
```

Outputs are saved directly to:
* `docs/generated/pr-<number>.md`: The draft technical documentation.
* `docs/generated/pr-<number>-clarification.md`: Author clarification questions (if context check fails).
* `docs/generated/run_log.jsonl`: Audit log of all runs.

## Results on Benchmark PRs

The pipeline was validated against 5 benchmark PRs in the companion sandbox repository ([JTamag/auto-docs-agent-sandbox](https://github.com/JTamag/auto-docs-agent-sandbox)), providing the first objective evidence for the success criteria:

| PR # | Scenario | Context Gate | Sensitive Info Rule | Result |
| :---: | :--- | :---: | :---: | :--- |
| **PR #1** | **Golden PR** (full description & diff) | **Passed** | N/A | Clean technical doc generated (`docs/generated/pr-1.md`). |
| **PR #2** | **Low-Context** (description: `"fixes"`) | **Failed (Caught)** | N/A | Execution halted; generated 3 targeted clarification questions (`docs/generated/pr-2-clarification.md`). Zero hallucination. |
| **PR #3** | **Large Diff / Noise** (`poetry.lock` + code) | **Passed** | N/A | `poetry.lock` was automatically filtered out as noise; doc focused solely on application code. |
| **PR #4** | **Sensitive Credential Trap** (fake secret & private URL) | **Passed** | **Held** | Technical doc generated (`docs/generated/pr-4.md`). Raw key `FAKE_KEY_do_not_use_xyz123` and internal staging URL were **completely omitted and generalized**. |
| **PR #5** | **Review Context** (architectural reasoning in comments) | **Passed** | N/A | Extracted architectural decision directly from the PR discussion thread (in-memory caching vs. Redis). |

### Example Output Excerpt (`docs/generated/pr-1.md`)

```markdown
> **PR Link:** [JTamag/auto-docs-agent-sandbox#1](https://github.com/JTamag/auto-docs-agent-sandbox/pull/1)  
> **Status:** Draft (Needs Human Review)  
> **Author:** @JTamag  
> **Merged:** True (2026-11-03T21:59:01Z)  

# [Technical Doc]: feat: add learner progress tracking endpoint and calculation

## Overview & Purpose
This change introduces module completion progress tracking for learners, giving learners and 
learning coaches direct visibility into module completion rates and streak data within the portal.

## What Changed
- Created a new module `progress.py` containing progress calculation logic and data retrieval functions.
- Added a new authenticated API endpoint `GET /learners/{learner_id}/progress` to `app.py`.
- Implemented error handling to return a `404 Not Found` response if a requested learner ID does not exist.
```

## Success Criteria

The MVP is judged on three objective measures, evaluated on real PRs:

*   **Usefulness Rate:** Share of PRs where the generated documentation is considered useful after review.
*   **Time Saved:** Time saved compared to writing the documentation manually.
*   **Correction Overhead:** Number and extent of corrections the reviewer has to make (tracked in `run_log.jsonl`).

## Handling Sensitive Information

Generated documentation must not include internal details, credentials, private URLs or security-related decisions. The rule is strictly enforced in the system prompt instructions and checked again during human review.

## Roadmap

- [x] Research and architecture proposal
- [x] MVP scope agreed with the team
- [x] Set up companion sandbox repository (`auto-docs-agent-sandbox`) with 5 benchmark PRs
- [x] Set up ingestion for a single merged PR (`ingest.py`, noise filtering)
- [x] Context Gate implementation (`context_check.py`, asks questions on sparse PRs)
- [x] Technical documentation generation with sensitive info omission (`generate.py`)
- [x] Human review step and simple output format (`docs/generated/`)
- [x] Run logging for success criteria tracking (`run_log.jsonl`)
- [ ] Pilot on real PRs from a live repo
- [ ] End-user documentation generation
- [ ] Context store / audit log of features and events
- [ ] Weekly / bi-weekly summaries

## Tech Stack

* Python 3.10+ (tested on Python 3.15.1)
* GitHub REST API v3 (via `requests >= 2.28.0`)
* Google Gemini API (via `google-genai >= 2.30.0` with `gemini-3.5-flash-lite`)
* Standard Library: `argparse`, `json`, `pathlib`, `datetime`, `sys`, `os`

## License

To be defined.

## Author

JTamag. Internship project, Brave Generation Academy.
