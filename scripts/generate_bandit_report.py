#!/usr/bin/env python3
"""Turn Bandit's JSON output into a readable Markdown security report."""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def cell(value: Any) -> str:
    """Make a value safe to place inside a Markdown table cell."""
    return str(value if value is not None else "—").replace("|", "\\|").replace("\r", " ").replace("\n", " ").strip()


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: generate_bandit_report.py <bandit-json> <markdown-output>", file=sys.stderr)
        return 2

    json_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    try:
        payload = json.loads(json_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Could not read Bandit JSON report: {exc}", file=sys.stderr)
        return 1

    findings = payload.get("results", [])
    if not isinstance(findings, list):
        print("Invalid Bandit JSON: 'results' must be a list.", file=sys.stderr)
        return 1

    severity_counts = Counter(
        str(item.get("issue_severity", "UNDEFINED")).upper()
        for item in findings
    )
    confidence_counts = Counter(
        str(item.get("issue_confidence", "UNDEFINED")).upper()
        for item in findings
    )

    generated = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    commit = os.getenv("GITHUB_SHA", "local run (commit not supplied)")
    lines = [
        "# Bandit Security Scan Report",
        "",
        f"**Generated:** {generated}  ",
        f"**Commit scanned:** `{cell(commit)}`  ",
        "**Scan scope:** Python source under `src/`  ",
        f"**Overall result:** **{len(findings)} finding(s)**",
        "",
        "## 1. Summary",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Total findings | {len(findings)} |",
    ]

    for severity in ("HIGH", "MEDIUM", "LOW", "UNDEFINED"):
        lines.append(f"| {severity.title()} severity | {severity_counts.get(severity, 0)} |")

    lines.extend([
        "",
        "### Confidence",
        "",
        "| Confidence | Count |",
        "|---|---:|",
    ])
    for confidence in ("HIGH", "MEDIUM", "LOW", "UNDEFINED"):
        lines.append(f"| {confidence.title()} | {confidence_counts.get(confidence, 0)} |")

    lines.extend(["", "## 2. Findings", ""])
    if not findings:
        lines.append("Bandit reported **no findings** in the scanned Python source for this run.")
    else:
        lines.extend([
            "| Severity | Confidence | Rule ID | Location | Finding |",
            "|---|---|---|---|---|",
        ])
        ordered = sorted(
            findings,
            key=lambda item: (
                {"HIGH": 0, "MEDIUM": 1, "LOW": 2}.get(
                    str(item.get("issue_severity", "")).upper(), 3
                ),
                str(item.get("filename", "")),
                int(item.get("line_number", 0) or 0),
            ),
        )
        for item in ordered:
            location = f"{item.get('filename', 'unknown')}:{item.get('line_number', '?')}"
            lines.append(
                "| "
                + " | ".join([
                    cell(str(item.get("issue_severity", "Undefined")).title()),
                    cell(str(item.get("issue_confidence", "Undefined")).title()),
                    f"`{cell(item.get('test_id', '—'))}`",
                    f"`{cell(location)}`",
                    cell(item.get("issue_text", "No description supplied")),
                ])
                + " |"
            )

    lines.extend([
        "",
        "## 3. How the scan is performed",
        "",
        "Bandit statically analyses the Python source code. It checks code patterns against security rules without running the application.",
        "",
        "The CI workflow generates JSON and HTML outputs and converts the JSON findings into this Markdown report. The normal Bandit check is also run separately so its exit status can determine whether the CI security step passes.",
        "",
        "```bash",
        "python -m bandit -r src -f json -o bandit-report.json --exit-zero",
        "python -m bandit -r src -f html -o bandit-report.html --exit-zero",
        "python -m bandit -q -r src",
        "```",
        "",
        "## 4. How to interpret the report",
        "",
        "- **Severity** describes the potential impact of a finding (High, Medium or Low).",
        "- **Confidence** describes how confident Bandit is that the reported code pattern is an issue.",
        "- **Rule ID** identifies the Bandit security test that detected the pattern.",
        "- **Location** identifies the source file and line to review.",
        "- A finding should be reviewed by a developer; some results may be false positives or require context.",
        "",
        "Bandit is a static-analysis tool, not a proof that the application is secure. A report with zero findings means that this Bandit scan did not identify patterns covered by its rules; it does not mean that the system has no vulnerabilities.",
        "",
        "## 5. Scope and limitations",
        "",
        "- This scan covers Python source under `src/`. It does not scan the root Streamlit file `app.py` unless the workflow scope is expanded.",
        "- Bandit analyses project source code; it does not check third-party package advisories. The separate `pip-audit` CI step performs dependency vulnerability checks.",
        "- This report is refreshed by GitHub Actions on pushes to `main`. Pull-request runs also produce downloadable JSON and HTML report files as workflow artifacts.",
        "- Review this report alongside code review, automated tests, dependency auditing and manual security testing.",
        "",
        "**Workflow configuration:** `.github/workflows/ci.yml`  ",
        "**Dependency audit:** `pip-audit`  ",
        "**Report generator:** `scripts/generate_bandit_report.py`",
        "",
    ])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote Bandit report to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
