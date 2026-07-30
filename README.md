# Auto Docs Agent
 
An agentic pipeline that automatically generates developer and end-user documentation from GitHub Pull Request context. Internship project for Brave Generation Academy.
 
## Overview
 
This project explores building an agentic pipeline capable of automatically generating documentation from software development context, primarily GitHub Pull Requests.
 
The system produces two types of documentation from a single source of truth:
 
*   **Technical documentation**, for developers. Focuses on architecture, implementation details, technical decisions, and information relevant to maintaining the code.
*   **Non-technical documentation**, for end users (Learners, Learning Coaches, Course Managers, etc.). Explains new features, changes, or improvements in plain, accessible language tailored to these specific personas.
## Status
 
**Current phase:** Research and architecture proposal.
 
This repository currently contains the investigation and proposed architecture, not a finished implementation. The goal of this phase is to:
1.  Survey possible approaches to generating documentation from PR context.
2.  Identify key challenges.
3.  Propose a system architecture.
4.  Get feedback before moving to MVP implementation.
**Next step:** Review this proposal with the team to finalize the architecture and define the exact scope of the MVP.
 
## Motivation
 
Keeping documentation up to date is a recurring problem in software teams. It's manual, easy to skip, and often drifts out of sync with the actual code. This project investigates whether an agentic system can reliably close that gap by using PRs (and possibly other sources) as context, producing consistent, audience-appropriate documentation with minimal human effort.
 
## Why an Agentic Pipeline
 
Rather than a single prompt-to-output call, the system is composed of specialized stages, each responsible for a distinct decision:
 
1.  **An Analysis Agent** interprets the diff and surrounding context to extract technical and business implications.
2.  **Two Generation Agents** take that analysis and produce audience-specific documentation: one for developers, and one explicitly instructed to write for BGA's end users (Learners, LCs, CMs).
3.  **A Context Store** feeds historical project knowledge into each stage, so decisions aren't made from the PR in isolation.
This separation of concerns is what makes the system agentic rather than a single static prompt. Each stage reasons over context and hands structured output to the next, instead of a script calling an API once.
 
## Approaches Considered
 
| Approach | Description | Trade-offs |
| :--- | :--- | :--- |
| **Direct prompting** | Feed PR description, diff, and comments directly to an LLM with a single well-crafted prompt. | Simple to build, but fragile when PRs have weak descriptions. |
| **RAG / Context store** | Maintain a database of past features, decisions, and events; agent retrieves relevant context before generating new docs. | More robust, better long-term consistency, more infrastructure to build. |
| **Multi-agent pipeline** | One agent analyzes the diff for technical/business implications; a second agent generates audience-specific docs from that analysis. | Cleaner separation of concerns, easier to debug and tune each stage independently. |
| **Template-driven** | Different templates per change type (new feature, bugfix, refactor, breaking change) guide what the agent should extract and report. | Improves consistency, but requires maintaining a template library. |
 
**Proposed direction:** A multi-agent pipeline combined with a context store (RAG) and templates per change type. See *Proposed Architecture* below.
 
## Key Challenges
 
*   **Inconsistent PR quality.** Not every PR has a clear description; the agent needs a strategy for low-context PRs.
*   **Signal vs. noise in diffs.** Distinguishing business-logic-relevant changes from formatting or refactors.
*   **Missing business context.** The reasoning behind a feature often lives outside the PR (issue tracker, chat, spec docs), not just in the code.
*   **Audience separation.** The technical version shouldn't be vague, and the non-technical version shouldn't leak implementation jargon to Learners or LCs.
*   **Accuracy and hallucination risk.** Incorrect documentation is worse than none; needs a review step, at least in the MVP.
*   **Continuity over time.** For weekly or bi-weekly summaries, the agent needs to track what's already been documented.
*   **Sensitive information.** Some PR content may not be appropriate for user-facing docs.
## Proposed Architecture
 
```text
GitHub PR (merged)
   |
   v
Trigger (GitHub Action / Webhook)
   |
   v
Ingestion: collects PR description, diff, comments, linked issues
   |
   v
Context Store / Audit Log (DB): stores history of features and events
   |
   v
Analysis Agent: cross-references diff and historical context,
                 extracts technical and business implications
   |
   |--> Technical Doc Agent: developer-facing documentation
   |--> Non-technical Doc Agent: end-user-facing documentation (Learners, LCs, CMs)
   |
   v
Output: committed to /docs, wiki, or sent via email
 
(optional) Summary Agent: aggregates audit log,
           sends weekly / bi-weekly digest email
```
 
## Roadmap
 
- [x] Finalize architecture proposal (Current phase)
- [ ] Review proposal with the team and define MVP scope
- [ ] Define audit log / context store schema
- [ ] Build MVP: single PR to technical doc 
- [ ] Add non-technical doc generation
- [ ] Add context store / retrieval
- [ ] Pilot on real PRs from a live repo
- [ ] Add weekly / bi-weekly summary reports
- [ ] Add automated email delivery
## Open Questions
 
*   Which additional context sources beyond PRs are worth integrating first: issues, commit messages, Slack?
*   Where should generated docs live: repo `/docs` folder, wiki, or external tool?
*   What's the review/approval step before docs are published?
*   What defines "done" for the MVP vs. the pilot?
## Tech Stack
 
To be defined during MVP planning.
 
## License
 
Brave Generation Academy. All rights reserved. Internal use only. This project is developed as part of an internship and intended for use by Brave Generation Academy.
 
## Author
 
Joao. Internship project, Brave Generation Academy.
