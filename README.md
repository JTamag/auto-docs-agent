# Auto Docs Agent

An agentic pipeline that generates developer and end-user documentation from GitHub Pull Request context. Internship project for Brave Generation Academy.

Status: architecture agreed, MVP in development.

## Overview

When a team builds a feature, most of the reasoning behind it ends up in the PR: the description, the diff, the review comments. Once the PR is merged that context gets buried, and the documentation is either written by hand later or never written at all.

This project explores whether a PR can be turned into useful documentation automatically, for two different audiences:

*   **Technical documentation** for developers: architecture, implementation details and technical decisions that matter when maintaining the code.
*   **Non-technical documentation** for end users (Learners, Learning Coaches, Course Managers): what changed and what it means for them, in plain language.

The first version only covers the technical documentation. End-user docs come later (see the roadmap).

## MVP scope

The MVP is deliberately small. It should be the minimum that already delivers value:

1.  Take a single merged PR.
2.  Read its title, description, diff and comments.
3.  Generate technical documentation.
4.  Save it somewhere simple, first a folder in the repo, later possibly a draft PR.
5.  Require human review before anything is published.

If a PR does not contain enough information to document it properly, the agent asks for more context instead of filling the gaps with guesses.

Everything else (end-user docs, the context store, weekly summaries, other context sources) is intentionally left out until this works end to end.

## Approach

The simplest way to do this is a single prompt: send the PR to an LLM and get a document back. It is the fastest to build, but it depends entirely on the quality of the PR. A thin description produces thin documentation.

The target architecture avoids that by splitting the work into stages:

*   An analysis stage reads the diff and surrounding context and works out what changed, technically and in terms of business logic.
*   Separate generation stages write for each audience, so the developer version and the end-user version do not compromise each other.
*   A context store keeps a history of past features and decisions, so a new PR is not analyzed in isolation.

Templates per change type (new feature, bugfix, refactor, breaking change) can sit on top of this to keep outputs consistent. The MVP starts with the smallest useful slice of this and grows towards it, rather than building all of it up front.

## Architecture

MVP flow:

```text
GitHub PR (merged)
   |
   v
Ingestion: title, description, diff, comments
   |
   v
Enough context to document?
   |-- no  --> ask for more context
   |
   v
Technical documentation generation
   |
   v
Draft output (folder in the repo, or draft PR)
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

## Key challenges

PR quality varies a lot, and some PRs are little more than a title and a diff. The agent needs to recognize when there is not enough to work with and ask, instead of inventing documentation.

Diffs also mix signal and noise. A formatting change and a business-logic change can look similar, and the documentation should only cover what matters.

Part of the reasoning behind a feature often lives outside the PR, in issues, chat or specs. This is why issues and commit messages are the first extra sources to consider.

Writing for two audiences from one source is harder than it sounds: the developer version should not be vague, and the end-user version should not leak implementation details.

Incorrect documentation is worse than none, which is why human review is part of the MVP and not an optional extra.

## Success criteria

The MVP will be judged on a small set of objective measures, evaluated on real PRs:

*   Share of PRs where the generated documentation is considered useful after review
*   Time saved compared to writing the documentation manually
*   Number of corrections the reviewer has to make

Target values will be agreed once there is a first baseline.

## Handling sensitive information

Generated documentation must not include internal details, credentials, private URLs or security-related decisions. The rule is applied in the prompt and checked again during human review, and it should be defined before the first real PR is processed, not added afterwards.

## Roadmap

- [x] Research and architecture proposal
- [x] MVP scope agreed with the team
- [ ] Set up ingestion for a single merged PR
- [ ] Technical documentation generation
- [ ] Handling of low-context PRs
- [ ] Sensitive information rule
- [ ] Human review step and simple output format
- [ ] Evaluate against the success criteria
- [ ] End-user documentation
- [ ] Context store
- [ ] Weekly / bi-weekly summaries

## Open questions

*   Which repository and sample PRs will be used for testing?
*   Which LLM provider and API access will be used?
*   Is a folder in the repo enough for the first output, or should it be a draft PR from the start?
*   What counts as "useful" in the success criteria, and who judges it?

## Tech stack

Not decided yet.

## License

To be defined.

## Author

JTamag. Internship project, Brave Generation Academy.