import argparse
from pathlib import Path
import re
from ast_rule_engine.cli import run_cli, Options


_no_match = re.compile(r"^\b$")


parser = argparse.ArgumentParser("ast_rule_engine")
parser.add_argument(
    "root",
    default=Path("."),
    help="Root folder where to apply the glob pattern",
    type=Path,
)
parser.add_argument(
    "--spec",
    "-s",
    required=True,
    type=Path,
    help="Path to the YAML search specification",
)
parser.add_argument(
    "--include", "-i", default="**/*.py", help="Glob pattern for files to search in"
)
parser.add_argument(
    "--exclude",
    "-x",
    default=_no_match,
    help="Exceptions to the `include` pattern (regexp for the path)",
    type=re.compile,
)
parser.add_argument(
    "--select",
    default=re.compile(r"[A-Z].*"),
    help="Rules to report (regexp)",
    type=re.compile,
)
parser.add_argument(
    "--unselect",
    default=_no_match,
    help="Rules to exclude from reporting (regexp)",
    type=re.compile,
)

args = parser.parse_args()
options = Options(
    spec_path=args.spec,
    root_dir=args.root,
    inclue_glob=args.include,
    exclude_pattern=args.exclude,
    select=args.select,
    unselect=args.unselect,
)

run_cli(options)
