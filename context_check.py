"""
Context Gate for Auto Docs Agent.

Evaluates whether a PR contains sufficient description and context to document reliably.
If context is lacking, generates specific questions for the PR author instead of hallucinating.
"""

from typing import Any, Dict, List, Tuple

TRIVIAL_WORDS = {
    "fixes", "fix", "update", "updates", "test", "wip", "todo", "done",
    "changes", "patch", "n/a", "none", "bugfix", "refactor"
}

def is_trivial_text(text: str) -> bool:
    """Check if a description is effectively empty or contains only placeholder words."""
    cleaned = text.strip().lower()
    if not cleaned:
        return True
    words = [w.strip(".,!-:;()") for w in cleaned.split() if w.strip(".,!-:;()")]
    if len(words) <= 3 and all(w in TRIVIAL_WORDS for w in words):
        return True
    return len(words) < 5

def evaluate_pr_context(pr: Dict[str, Any]) -> Tuple[bool, str, List[str]]:
    """
    Evaluate if the PR has enough context to document.

    Returns:
        (passed, reason, questions_for_author)
    """
    desc = pr.get("description", "").strip()
    files = [f for f in pr.get("files", []) if not f.get("is_ignored")]
    comments = pr.get("comments", [])

    # Substantive discussion comments can provide the context missing from description
    has_substantive_comment = any(len(c.get("body", "").split()) >= 8 for c in comments)

    if not is_trivial_text(desc):
        return True, "PR description provides sufficient context.", []

    if has_substantive_comment:
        return True, "PR comments provide sufficient context to explain the change.", []

    # If both description and comments lack context, build targeted questions
    file_names = [f["filename"] for f in files]
    questions = []

    if file_names:
        questions.append(
            f"What specific feature, bug, or requirement prompted the changes in {', '.join(file_names[:3])}?"
        )
    else:
        questions.append("What was the primary objective of this PR?")

    questions.append("Are there any operational requirements, breaking changes, or dependencies introduced?")
    questions.append("What expected behavior should developers or testers verify when maintaining this code?")

    return False, "PR description is missing or trivial, and no explanatory comments were found.", questions

