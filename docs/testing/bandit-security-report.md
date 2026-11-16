# Bandit Security Scan Report

**Generated:** 2026-11-16 10:21:51 UTC  
**Commit scanned:** `b213e6ba0c13192c5ee1519db0f8bd00c44ce371`  
**Scan scope:** Python source under `src/`  
**Overall result:** **0 finding(s)**

## 1. Summary

| Measure | Count |
|---|---:|
| Total findings | 0 |
| High severity | 0 |
| Medium severity | 0 |
| Low severity | 0 |
| Undefined severity | 0 |

### Confidence

| Confidence | Count |
|---|---:|
| High | 0 |
| Medium | 0 |
| Low | 0 |
| Undefined | 0 |

## 2. Findings

Bandit reported **no findings** in the scanned Python source for this run.

## 3. How the scan is performed

Bandit statically analyses the Python source code. It checks code patterns against security rules without running the application.

The CI workflow generates JSON and HTML outputs and converts the JSON findings into this Markdown report. The normal Bandit check is also run separately so its exit status can determine whether the CI security step passes.

```bash
python -m bandit -r src -f json -o bandit-report.json --exit-zero
python -m bandit -r src -f html -o bandit-report.html --exit-zero
python -m bandit -q -r src
```

## 4. How to interpret the report

- **Severity** describes the potential impact of a finding (High, Medium or Low).
- **Confidence** describes how confident Bandit is that the reported code pattern is an issue.
- **Rule ID** identifies the Bandit security test that detected the pattern.
- **Location** identifies the source file and line to review.
- A finding should be reviewed by a developer; some results may be false positives or require context.

Bandit is a static-analysis tool, not a proof that the application is secure. A report with zero findings means that this Bandit scan did not identify patterns covered by its rules; it does not mean that the system has no vulnerabilities.

## 5. Scope and limitations

- This scan covers Python source under `src/`. It does not scan the root Streamlit file `app.py` unless the workflow scope is expanded.
- Bandit analyses project source code; it does not check third-party package advisories. The separate `pip-audit` CI step performs dependency vulnerability checks.
- This report is refreshed by GitHub Actions on pushes to `main`. Pull-request runs also produce downloadable JSON and HTML report files as workflow artifacts.
- Review this report alongside code review, automated tests, dependency auditing and manual security testing.

**Workflow configuration:** `.github/workflows/ci.yml`  
**Dependency audit:** `pip-audit`  
**Report generator:** `scripts/generate_bandit_report.py`
