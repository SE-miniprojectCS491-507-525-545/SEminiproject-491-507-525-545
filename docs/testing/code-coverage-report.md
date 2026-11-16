# Code Coverage Report

**Project:** Railway Reservation System  
**Report date:** 16 November 2026  
**Coverage result:** **94.38%**  
**Verification:** GitHub Actions CI — successful

## 1. Coverage summary

The automated test suite achieved **94.38% code coverage**, which is above the project's configured minimum of **80%**.

| Measurement | Result |
|---|---:|
| Overall code coverage | **94.38%** |
| Minimum coverage required by CI | 80% |
| Test cases collected and passed | 446 passed |
| Failed tests | 0 |
| Source statements measured | 1,137 |
| Statements not executed | 53 |
| Branches measured | 304 |
| Partially covered branches | 26 |
| Test execution time | 5.54 seconds |

The percentage and counts above are taken from the successful GitHub Actions run linked below. They are a dated result for the tested commit, not a claim that every future commit will have the same percentage.

**CI run:** [View the GitHub Actions run](https://github.com/SE-miniprojectCS491-507-525-545/SEminiproject-491-507-525-545/actions/runs/43827104527)  
**Tested commit:** `edb4f138bab5d641b420806cafb9098a2b39c28b` (the changes from this commit were merged into `main`).

## 2. How code coverage was obtained

Code coverage tells us how much of the source code was executed while the automated tests were running. It helps identify code paths that may not have been exercised by the test suite.

This project uses:

- **pytest** to discover and run the automated tests in the `tests/` directory.
- **pytest-cov** to collect coverage information while pytest runs.
- **Coverage.py** underneath pytest-cov to measure executed statements and branches.
- **Branch coverage** to consider decision paths such as the true and false sides of conditional logic.

### Dependencies

The coverage tools are included in `requirements-dev.txt`:

```text
pytest
pytest-cov
```

Install the development dependencies from the repository root:

```bash
python -m pip install -r requirements-dev.txt
```

### Command used by GitHub Actions

The CI workflow at `.github/workflows/ci.yml` runs this command:

```bash
python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
```

What each option does:

| Option | Purpose |
|---|---|
| `--cov=src` | Measures coverage for the Python source code under `src/` (the `railway` package). |
| `--cov-branch` | Enables branch coverage as well as statement coverage. |
| `--cov-report=term-missing` | Prints the coverage summary in the CI terminal log and lists source lines that were not executed. |
| `--cov-fail-under=80` | Fails the test command if total coverage is below 80%. |

To reproduce the CI coverage check locally, run the same command from the repository root after installing `requirements-dev.txt`:

```bash
PYTHONPATH=src python -m pytest --cov=src --cov-branch --cov-report=term-missing --cov-fail-under=80
```

The workflow runs on pushes and pull requests. In addition to the coverage-enabled test command, it runs Bandit security checks and a dependency audit.

## 3. Coverage by source file

The following figures are copied from the coverage table produced by the successful CI run.

| Source file | Statements | Missed | Branches | Partial branches | Coverage |
|---|---:|---:|---:|---:|---:|
| `src/railway/__init__.py` | 0 | 0 | 0 | 0 | 100% |
| `src/railway/__main__.py` | 3 | 3 | 2 | 0 | 0% |
| `src/railway/access.py` | 22 | 0 | 12 | 0 | 100% |
| `src/railway/auth.py` | 55 | 2 | 22 | 0 | 97% |
| `src/railway/availability.py` | 53 | 0 | 10 | 0 | 100% |
| `src/railway/backup.py` | 56 | 8 | 10 | 3 | 83% |
| `src/railway/booking.py` | 50 | 0 | 8 | 0 | 100% |
| `src/railway/booking_views.py` | 39 | 0 | 10 | 0 | 100% |
| `src/railway/cancellation.py` | 75 | 1 | 16 | 1 | 98% |
| `src/railway/cli.py` | 306 | 34 | 78 | 18 | 86% |
| `src/railway/consistency.py` | 20 | 0 | 10 | 0 | 100% |
| `src/railway/dates.py` | 12 | 0 | 6 | 0 | 100% |
| `src/railway/demo_data.py` | 25 | 0 | 8 | 0 | 100% |
| `src/railway/models.py` | 42 | 0 | 0 | 0 | 100% |
| `src/railway/perf.py` | 8 | 0 | 0 | 0 | 100% |
| `src/railway/pnr.py` | 11 | 0 | 4 | 0 | 100% |
| `src/railway/registration.py` | 31 | 0 | 14 | 0 | 100% |
| `src/railway/search.py` | 32 | 0 | 12 | 0 | 100% |
| `src/railway/search_help.py` | 46 | 0 | 18 | 0 | 100% |
| `src/railway/seats.py` | 9 | 0 | 4 | 0 | 100% |
| `src/railway/security.py` | 15 | 0 | 0 | 0 | 100% |
| `src/railway/storage.py` | 177 | 5 | 38 | 4 | 96% |
| `src/railway/traveller_validation.py` | 50 | 0 | 22 | 0 | 100% |
| **TOTAL** | **1,137** | **53** | **304** | **26** | **94.38%** |

## 4. Understanding the result

A coverage value of 94.38% means that the tests exercised most of the measured source code and branch paths during this run. It does **not** mean that 94.38% of all possible bugs have been found or that every requirement has passed acceptance testing.

Coverage also has a defined scope: the CI command uses `--cov=src`, so this measurement covers the Python package in `src/`. The root-level Streamlit frontend, `app.py`, is not included in this percentage. Browser-based UI testing should therefore be tracked separately.

Some files have less than 100% coverage, including `__main__.py`, `backup.py`, `cli.py`, `auth.py`, `cancellation.py` and `storage.py`. The terminal report identifies the lines and branch paths that were not exercised, which can guide future test improvements.

## 5. Keeping this report up to date

This Markdown file records the result from the CI run on **16 November 2026**. The coverage command runs automatically in CI, but this document's displayed percentage is a manually recorded snapshot. When a later CI run becomes the reference result:

1. Open the successful GitHub Actions run for the relevant commit.
2. Find the `Run tests with coverage` step.
3. Record its total coverage, test count, execution time and per-file figures.
4. Update the summary and file table in this report, including the run date and commit SHA.
5. Do not replace the result with a local run unless its command, source revision and environment are recorded.

---

**Report location:** `docs/testing/code-coverage-report.md`  
**Coverage configuration:** `.github/workflows/ci.yml`  
**Test suite:** `tests/`
