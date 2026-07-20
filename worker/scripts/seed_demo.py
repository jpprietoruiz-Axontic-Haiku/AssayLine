"""Seed the demo dataset: spec profiles + 4 synthetic reports (already
extracted, no Anthropic API call needed). Run with:

    cd worker && python -m scripts.seed_demo
"""

from app.core.db import get_session_factory
from app.demo.seed import run_seed


def main() -> None:
    session_factory = get_session_factory()
    with session_factory() as db:
        created = run_seed(db)
        print(f"seeded {len(created)} demo report(s) (already-existing ones were skipped)")


if __name__ == "__main__":
    main()
