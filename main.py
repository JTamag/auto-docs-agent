"""
Main CLI entrypoint for Auto Docs Agent.

Orchestrates ingestion, context check, technical doc generation,
output writing, and run logging.
"""

import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sys

from ingest import fetch_pr, load_env_file
from context_check import evaluate_pr_context
from generate import generate_technical_doc

load_env_file()

def log_run(log_file: Path, entry: dict) -> None:
    """Append a run event to the JSONL run log."""
    log_file.parent.mkdir(parents=True, exist_ok=True)
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")

def run_pipeline(repo: str, pr_number: int, output_dir: str = "docs/generated") -> int:
    """Run the end-to-end documentation generation pipeline for a PR."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    log_file = out_path / "run_log.jsonl"

    print(f"\n[1/3] Ingesting PR #{pr_number} from {repo}...")
    try:
        pr_data = fetch_pr(repo=repo, pr_number=pr_number)
    except Exception as e:
        print(f"Error fetching PR: {e}", file=sys.stderr)
        return 1

    print(f"      Title:  {pr_data['title']}")
    print(f"      Author: {pr_data['author']}")
    print(f"      Files:  {len(pr_data['files'])} changed")

    print("\n[2/3] Evaluating PR context via Context Gate...")
    passed, reason, questions = evaluate_pr_context(pr_data)

    if not passed:
        print("      --> CONTEXT CHECK FAILED.")
        print(f"      Reason: {reason}")
        print("\n      Action: Generating clarification request for PR author instead of documentation:")
        for idx, q in enumerate(questions, 1):
            print(f"      {idx}. {q}")

        # Write clarification request document
        clarification_file = out_path / f"pr-{pr_number}-clarification.md"
        content = f"""# Context Request: PR #{pr_number} - {pr_data['title']}

> **PR Link:** [{repo}#{pr_number}]({pr_data['url']})  
> **Author:** @{pr_data['author']}  
> **Status:** Insufficient context to generate reliable documentation.  

### Why this was triggered:
{reason}

### Questions for the Author:
""" + "\n".join(f"{i}. {q}" for i, q in enumerate(questions, 1))

        clarification_file.write_text(content, encoding="utf-8")
        print(f"\n      Saved clarification request to: {clarification_file}")

        log_run(log_file, {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "repo": repo,
            "pr": pr_number,
            "passed_context_check": False,
            "reason": reason,
            "questions_count": len(questions),
            "output_file": str(clarification_file),
            "reviewer_corrections": None
        })
        return 0

    print("      --> Context check PASSED.")
    print("\n[3/3] Generating technical documentation via Gemini 3.8 Flash...")
    try:
        doc_body = generate_technical_doc(pr_data)
    except Exception as e:
        print(f"Error during document generation: {e}", file=sys.stderr)
        return 1

    doc_file = out_path / f"pr-{pr_number}.md"
    header = f"""> **PR Link:** [{repo}#{pr_number}]({pr_data['url']})  
> **Status:** Draft (Needs Human Review)  
> **Author:** @{pr_data['author']}  
> **Merged:** {pr_data['is_merged']} ({pr_data.get('merged_at') or 'N/A'})  
> **Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}  

---

"""
    full_doc = header + doc_body
    doc_file.write_text(full_doc, encoding="utf-8")

    print(f"      --> Documentation generated successfully!")
    print(f"      Saved draft document to: {doc_file}")

    log_run(log_file, {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "repo": repo,
        "pr": pr_number,
        "passed_context_check": True,
        "output_file": str(doc_file),
        "reviewer_corrections": None
    })
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Auto Docs Agent: End-to-end PR documentation generator.")
    parser.add_argument("--repo", default="JTamag/auto-docs-agent-sandbox", help="GitHub repo 'owner/name'")
    parser.add_argument("--pr", type=int, required=True, help="PR number to document")
    parser.add_argument("--output-dir", default="docs/generated", help="Directory where draft docs are saved")

    args = parser.parse_args()
    sys.exit(run_pipeline(repo=args.repo, pr_number=args.pr, output_dir=args.output_dir))

