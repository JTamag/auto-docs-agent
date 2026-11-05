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
1. Ensure `GITHUB_TOKEN` and `GEMINI_API_KEY` are defined in `.env` (or environment variables).
2. Install dependencies:
   ```bash
   pip install requests google-genai
   ```

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

* Python 3.15
* GitHub REST API (via `requests`)
* Google Gemini API (via `google-genai` with `gemini-3.5-flash-lite` / `gemini-3.8-flash`)

## License

To be defined.

## Author

JTamag. Internship project, Brave Generation Academy.
