#!/usr/bin/env python3
"""Simple pre-commit scanner to detect banned patterns in staged files.

This script checks staged changes for:
- occurrences of 'gsk' or 'gsk.com'
- email addresses matching the user's GSK address pattern
- OpenAI-style API keys starting with sk- (common accidental leak)
- obvious test passwords like 'TestPassword123' or 'YourPassword123'

It returns non-zero and prints offending files/patterns to block the commit.
"""
import re
import subprocess
import sys

PATTERNS = [
    (re.compile(r"\bgsk\b", re.IGNORECASE), "GSK org reference"),
    (re.compile(r"[\w.+-]+@gsk\.com", re.IGNORECASE), "GSK email address"),
    (re.compile(r"sk-[A-Za-z0-9_\-]{20,}"),
     "Potential OpenAI API key (sk-...)"),
    (re.compile(r"TestPassword123|YourPassword123|YourSecurePasswordHere"),
     "Known test password"),
]


def get_staged_files():
    res = subprocess.run(
        ["git", "diff", "--cached", "--name-only"], capture_output=True, text=True)
    if res.returncode != 0:
        print("Failed to get staged files")
        sys.exit(1)
    return [f for f in res.stdout.splitlines() if f.strip()]


def scan_file(path):
    try:
        with open(path, "r", errors="ignore") as fh:
            content = fh.read()
    except Exception:
        return []
    hits = []
    for pat, name in PATTERNS:
        if pat.search(content):
            hits.append((name, pat.pattern))
    return hits


def main():
    staged = get_staged_files()
    if not staged:
        return 0

    blocked = {}
    for path in staged:
        hits = scan_file(path)
        if hits:
            blocked[path] = hits

    if blocked:
        print("Pre-commit check failed — potential secrets or banned patterns detected:")
        for path, hits in blocked.items():
            print(f" - {path}:")
            for name, pat in hits:
                print(f"    - {name}: pattern {pat}")
        print("\nPlease remove these items or move secrets to environment configuration/Key Vault before committing.")
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
