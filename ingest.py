"""
Ingestion module for Auto Docs Agent.

Fetches PR title, description, diff, changed files, and comments
from the GitHub REST API without requiring any LLM.
"""

import argparse
import json
import os
from pathlib import Path
import sys
from typing import Any, Dict, List, Optional
import requests

# Files commonly considered noise for documentation purposes
IGNORED_PATTERNS = {
    "package-lock.json",
    "yarn.lock",
    "pnpm-lock.yaml",
    "poetry.lock",
    "Pipfile.lock",
    "Cargo.lock",
    "composer.lock",
    "go.sum",
}

def load_env_file() -> None:
    """Simple .env loader if file exists."""
    for candidate in [Path(".env"), Path("auto-docs-agent/.env"), Path(__file__).parent / ".env"]:
        if candidate.exists():
            with open(candidate, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))
            break

load_env_file()

def is_noise_file(filename: str) -> bool:
    """Check if a file should be filtered out as noise."""
    basename = filename.split("/")[-1]
    if basename in IGNORED_PATTERNS:
        return True
    if basename.endswith(".min.js") or basename.endswith(".min.css"):
        return True
    if basename.endswith(".map"):
        return True
    return False

def get_headers(token: Optional[str] = None) -> Dict[str, str]:
    """Build request headers for GitHub API."""
    headers = {
        "Accept": "application/vnd.github.v3+json",
        "User-Agent": "auto-docs-agent",
    }
    github_token = token or os.getenv("GITHUB_TOKEN")
    if github_token:
        # Supports both classic and fine-grained tokens
        headers["Authorization"] = f"Bearer {github_token}"
    return headers

def fetch_pr(repo: str, pr_number: int, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch all relevant context for a GitHub Pull Request.

    Args:
        repo: Repository name in 'owner/name' format (e.g., 'JTamag/auto-docs-agent-sandbox')
        pr_number: Pull request number
        token: Optional GitHub personal access token

    Returns:
        Structured dictionary containing PR metadata, description, diffs, and comments.
    """
    base_url = f"https://api.github.com/repos/{repo}"
    headers = get_headers(token)

    # 1. Fetch core PR metadata
    pr_url = f"{base_url}/pulls/{pr_number}"
    resp = requests.get(pr_url, headers=headers)
    if resp.status_code == 404:
        raise ValueError(
            f"PR #{pr_number} not found in {repo}. "
            f"If the repository is private, ensure GITHUB_TOKEN is provided."
        )
    if resp.status_code == 403 and "rate limit" in resp.text.lower():
        raise PermissionError("GitHub API rate limit exceeded. Set GITHUB_TOKEN environment variable.")
    resp.raise_for_status()
    pr_data = resp.json()

    # 2. Fetch changed files and diff patches
    files_url = f"{base_url}/pulls/{pr_number}/files"
    files_resp = requests.get(files_url, headers=headers)
    files_resp.raise_for_status()
    raw_files = files_resp.json()

    files = []
    for f in raw_files:
        filename = f.get("filename", "")
        ignored = is_noise_file(filename)
        files.append({
            "filename": filename,
            "status": f.get("status"),
            "additions": f.get("additions", 0),
            "deletions": f.get("deletions", 0),
            "is_ignored": ignored,
            "patch": None if ignored else f.get("patch", "")
        })

    # 3. Fetch conversation comments (issue comments)
    issue_comments_url = f"{base_url}/issues/{pr_number}/comments"
    comments_resp = requests.get(issue_comments_url, headers=headers)
    comments_resp.raise_for_status()
    raw_issue_comments = comments_resp.json()

    # 4. Fetch inline code review comments
    review_comments_url = f"{base_url}/pulls/{pr_number}/comments"
    review_resp = requests.get(review_comments_url, headers=headers)
    review_resp.raise_for_status()
    raw_review_comments = review_resp.json()

    comments = []
    for c in raw_issue_comments:
        comments.append({
            "type": "conversation",
            "author": c.get("user", {}).get("login"),
            "body": c.get("body", "").strip(),
            "created_at": c.get("created_at")
        })

    for c in raw_review_comments:
        comments.append({
            "type": "code_review",
            "author": c.get("user", {}).get("login"),
            "path": c.get("path"),
            "line": c.get("line"),
            "body": c.get("body", "").strip(),
            "created_at": c.get("created_at")
        })

    return {
        "repo": repo,
        "pr_number": pr_number,
        "url": pr_data.get("html_url"),
        "title": pr_data.get("title", ""),
        "author": pr_data.get("user", {}).get("login"),
        "state": pr_data.get("state"),
        "is_merged": pr_data.get("merged", False),
        "merged_at": pr_data.get("merged_at"),
        "base_branch": pr_data.get("base", {}).get("ref"),
        "head_branch": pr_data.get("head", {}).get("ref"),
        "description": (pr_data.get("body") or "").strip(),
        "files": files,
        "comments": comments,
    }

def print_pr_summary(pr: Dict[str, Any]) -> None:
    """Print a clean human-readable summary of the ingested PR."""
    print("=" * 60)
    print(f"PR #{pr['pr_number']}: {pr['title']}")
    print(f"Repo:   {pr['repo']}")
    print(f"Author: {pr['author']} | Merged: {pr['is_merged']} ({pr.get('merged_at')})")
    print(f"Branch: {pr['head_branch']} -> {pr['base_branch']}")
    print(f"URL:    {pr['url']}")
    print("-" * 60)
    print("DESCRIPTION:")
    if pr["description"]:
        print(pr["description"])
    else:
        print("  [EMPTY / NO DESCRIPTION]")
    print("-" * 60)
    print(f"CHANGED FILES ({len(pr['files'])}):")
    for f in pr["files"]:
        status_tag = f"[{f['status'].upper()}]"
        diff_tag = f"+{f['additions']} -{f['deletions']}"
        noise_tag = " (IGNORED NOISE)" if f["is_ignored"] else ""
        print(f"  * {status_tag} {f['filename']} ({diff_tag}){noise_tag}")
        if not f["is_ignored"] and f["patch"]:
            lines = f["patch"].split("\n")
            preview = "\n    ".join(lines[:6])
            print(f"    {preview}")
            if len(lines) > 6:
                print(f"    ... (+{len(lines) - 6} more lines)")
    print("-" * 60)
    print(f"COMMENTS ({len(pr['comments'])}):")
    if not pr["comments"]:
        print("  [NO COMMENTS]")
    for idx, c in enumerate(pr["comments"], 1):
        c_type = "Review on " + c["path"] if c["type"] == "code_review" else "Conversation"
        print(f"  [{idx}] {c['author']} ({c_type}):")
        print(f"      {c['body']}")
    print("=" * 60)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Ingest GitHub PR context without an LLM.")
    parser.add_argument("--repo", default="JTamag/auto-docs-agent-sandbox", help="GitHub repo 'owner/name'")
    parser.add_argument("--pr", type=int, required=True, help="PR number to fetch")
    parser.add_argument("--token", default=None, help="GitHub token (or use GITHUB_TOKEN env var)")
    parser.add_argument("--json", action="store_true", help="Output raw JSON instead of text summary")

    args = parser.parse_args()

    try:
        data = fetch_pr(repo=args.repo, pr_number=args.pr, token=args.token)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print_pr_summary(data)
    except Exception as e:
        print(f"Error ingesting PR: {e}", file=sys.stderr)
        sys.exit(1)
