"""
Technical Documentation Generator for Auto Docs Agent.

Calls the Gemini API using google-genai to generate structured developer documentation
from ingested PR context while strictly omitting sensitive details.
"""

import os
from typing import Any, Dict
from google import genai
from ingest import load_env_file

load_env_file()

SYSTEM_INSTRUCTION = """You are an expert technical documentation writer for a software engineering team.
Your task is to write clean, accurate, developer-facing technical documentation from the provided GitHub Pull Request context.

Documentation Guidelines:
1. Audience: Software engineers who need to maintain, debug, and extend this codebase.
2. Tone: Direct, technical, and objective. Avoid marketing fluff, filler sentences, or generic introductions.
3. Grounding: Rely strictly on the provided context, diffs, and comments. DO NOT hallucinate features, endpoints, or dependencies not present in the PR.

MANDATORY SENSITIVE INFORMATION GUARDRAILS:
- STRICT RULE: You must NEVER include API keys, tokens, passwords, credentials, private/internal URLs, staging IPs/domains, or internal security debate details.
- If raw credentials, internal URLs (e.g., .internal, .local, 10.x.x.x, 192.168.x.x), or security bypass comments appear in the diff or context:
  * DO NOT quote or print them.
  * Generalize the concept (e.g., write "authenticates via an internal secret header" or "dispatches events to an internal webhook endpoint").

Document Structure:
Your output must use standard GitHub Flavored Markdown with these exact sections:

# [Technical Doc]: {PR Title}

## Overview & Purpose
A concise 2-3 sentence explanation of what this change accomplishes and why it was introduced.

## What Changed
Bullet points detailing the exact functional and architectural modifications.

## Implementation Details
Key components, functions, endpoints, data structures, or algorithms introduced or modified. Include short representative code snippets if helpful.

## Maintenance & Operational Notes
Caveats, configuration requirements, error handling, performance considerations (e.g., caching TTLs), or testing notes for developers maintaining this code.
"""

def generate_technical_doc(pr: Dict[str, Any]) -> str:
    """
    Generate technical documentation for an ingested PR using Gemini.
    """
    client = genai.Client()

    # Format files and diffs
    files_summary = []
    for f in pr.get("files", []):
        if f.get("is_ignored"):
            files_summary.append(f"- {f['filename']} (Noise/lockfile - diff ignored)")
        else:
            diff_text = f.get("patch") or "[No diff available]"
            files_summary.append(f"### File: {f['filename']} (+{f['additions']} -{f['deletions']})\n```diff\n{diff_text}\n```")

    comments_summary = []
    for c in pr.get("comments", []):
        comments_summary.append(f"- [{c['type'].upper()}] {c['author']}: {c['body']}")

    user_input = f"""Please generate the technical documentation for this Pull Request:

Repository: {pr.get('repo')}
PR Number: #{pr.get('pr_number')}
Title: {pr.get('title')}
Author: {pr.get('author')}
Branch: {pr.get('head_branch')} -> {pr.get('base_branch')}
Merged: {pr.get('is_merged')}

PR Description:
{pr.get('description') or '[No description provided]'}

PR Comments / Discussion:
{chr(10).join(comments_summary) if comments_summary else '[No comments]'}

Changed Files & Diffs:
{chr(10).join(files_summary)}
"""

    interaction = client.interactions.create(
        model="gemini-3.5-flash-lite",
        input=user_input,
        system_instruction=SYSTEM_INSTRUCTION
    )

    return interaction.output_text or ""
