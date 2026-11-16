# Bandit Security Scan Report

**Generated:** 2026-11-16 23:45:29 UTC  
**Commit scanned:** `8a95af98fcc46c990de2fd99af40beaf828d60af`  
**Scan scope:** Python source under `src/` and the root Streamlit `app.py`  
**Overall result:** **2 finding(s)**

## 1. Summary

| Measure | Count |
|---|---:|
| Total findings | 2 |
| High severity | 0 |
| Medium severity | 0 |
| Low severity | 2 |
| Undefined severity | 0 |

### Confidence

| Confidence | Count |
|---|---:|
| High | 0 |
| Medium | 2 |
| Low | 0 |
| Undefined | 0 |

## 2. Findings

| Severity | Confidence | Rule ID | Location | Finding |
|---|---|---|---|---|
| Low | Medium | `B105` | `src/railway/demo_data.py:14` | Possible hardcoded password: 'demo12345' |
| Low | Medium | `B105` | `src/railway/demo_data.py:16` | Possible hardcoded password: 'Admin12345' |

## 3. How the scan is performed

Bandit statically analyses the Python source code. It checks code patterns against security rules without running the application.

The CI workflow generates JSON and HTML outputs using `--ignore-nosec`, so the report also shows patterns on lines marked with `# nosec`. This is useful for transparency: these are still Bandit detections, even though the source contains an explicit suppression. The normal Bandit security gate is run separately without `--ignore-nosec`, so the standard suppression behavior remains in effect for the pass/fail check.

```bash
python -m bandit -r src app.py --ignore-nosec -f json -o bandit-report.json --exit-zero
python -m bandit -r src app.py --ignore-nosec -f html -o bandit-report.html --exit-zero
python -m bandit -q -r src app.py
```

## 4. How to interpret the report

- **Severity** describes the potential impact of a finding (High, Medium or Low).
- **Confidence** describes how confident Bandit is that the reported code pattern is an issue.
- **Rule ID** identifies the Bandit security test that detected the pattern.
- **Location** identifies the source file and line to review.
- A finding should be reviewed by a developer; some results may be false positives or require context.

Bandit is a static-analysis tool, not a proof that the application is secure. A report with zero findings means that this Bandit scan did not identify patterns covered by its rules; it does not mean that the system has no vulnerabilities.

## 5. Scope and limitations

- This scan covers the Python backend under `src/` and the root Streamlit frontend `app.py`.
- The report-generation scan uses Bandit `--ignore-nosec` so detections remain visible even where source comments explicitly suppress a rule. Review those findings in context; the normal CI security gate runs without that option and continues to honor the suppressions.
- Bandit analyses project source code; it does not check third-party package advisories. The separate `pip-audit` CI step performs dependency vulnerability checks.
- This report is refreshed by GitHub Actions on pushes to `main`. Pull-request runs also produce downloadable JSON and HTML report files as workflow artifacts.
- Review this report alongside code review, automated tests, dependency auditing and manual security testing.

**Workflow configuration:** `.github/workflows/ci.yml`  
**Dependency audit:** `pip-audit`  
**Report generator:** `scripts/generate_bandit_report.py`
