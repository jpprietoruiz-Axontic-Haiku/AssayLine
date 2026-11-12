# AssayLine — 2-minute technical review

**What it demonstrates:** extracting structured information from messy industrial and laboratory reports with a tool-using AI pipeline, explicit validation and human approval before export. This is a portfolio demonstration using **synthetic data**, not a deployed production service.

## Review the implementation

| Area | Where to look |
| --- | --- |
| Ingestion and worker | [FastAPI / Python worker](worker) |
| Web interface | [React dashboard](dashboard) |
| Validation and anomaly checks | [Worker application](worker/app) |
| Automated tests | [Python test suite](worker/tests) |
| Architecture and trade-offs | [DECISIONS.md](DECISIONS.md) |
| CI | [GitHub Actions workflow](.github/workflows/ci.yml) |

## Engineering highlights

- Tool-calling pipeline with deterministic unit conversion and numerical checks.
- Pydantic field-level validation instead of trusting raw LLM output.
- Out-of-specification checks recomputed after a reviewer edits extracted values.
- Asynchronous ingestion through Redis and RQ.
- Synthetic sample data and dashboard screenshots for reproducible demonstrations.

## Scope and limitations

The repository documents **49 Python tests** plus dashboard typechecking. Its current demo does not claim enterprise security, high-volume throughput or comprehensive accuracy on arbitrary industrial documents. See the limitations in [DECISIONS.md](DECISIONS.md). The CI workflow is configured to validate the repository's **master** branch and its pull requests.

**Author:** Juan Pablo Prieto, PhD · [GitHub profile](https://github.com/jpprietoruiz-Axontic-Haiku)
