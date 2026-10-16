"""
Writes the API's OpenAPI schema to docs/openapi.json.

The committed docs/openapi.json is what the documentation site renders, so it
must match the code. Regenerate it whenever routes, their docstrings or
parameters, or the moalmanac-db submodule change:

    python utils/export_openapi.py

With `--check`, nothing is written; the script exits with status 1 if the
committed file is out of date. CI runs it this way.
"""

import argparse
import importlib
import json
import os
import pathlib
import sys

REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPOSITORY_ROOT / "docs" / "openapi.json"


def main() -> int:
    """
    Generates the OpenAPI schema and writes it, or checks it against the
    committed file.

    Returns:
        int: The exit status: 0 on success, 1 if `--check` found the committed
            file out of date.
    """
    parser = argparse.ArgumentParser(description=__doc__.strip().splitlines()[0])
    parser.add_argument(
        "--check",
        action="store_true",
        help="Exit with status 1 if docs/openapi.json is out of date.",
    )
    arguments = parser.parse_args()

    # Run as `python -m utils.export_openapi`, this repository's utils/ is imported
    # as `utils` and hides moalmanac-db's utils package, which the app imports.
    if __package__:
        print(
            "Run this as `python utils/export_openapi.py`, not with `python -m`.",
            file=sys.stderr,
        )
        return 2

    serialized = render_schema()
    current = OUTPUT_PATH.read_text() if OUTPUT_PATH.exists() else None

    if arguments.check:
        if serialized != current:
            print(
                f"{OUTPUT_PATH.relative_to(REPOSITORY_ROOT)} is out of date. Run "
                "`python utils/export_openapi.py` and commit the result.",
                file=sys.stderr,
            )
            return 1
        print(f"{OUTPUT_PATH.relative_to(REPOSITORY_ROOT)} is up to date.")
        return 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(serialized)
    print(f"Wrote {OUTPUT_PATH.relative_to(REPOSITORY_ROOT)}.")
    return 0


def render_schema() -> str:
    """
    Builds the application and serializes its OpenAPI schema.

    `app.main` creates the application when imported, reading `config.ini` from
    the working directory, so this runs from the repository root.

    Returns:
        str: The schema as indented JSON, ending with a newline.
    """
    os.chdir(REPOSITORY_ROOT)
    if str(REPOSITORY_ROOT) not in sys.path:
        sys.path.insert(0, str(REPOSITORY_ROOT))
    application = importlib.import_module("app.main").app
    return json.dumps(application.openapi(), indent=2, ensure_ascii=False) + "\n"


if __name__ == "__main__":
    sys.exit(main())
