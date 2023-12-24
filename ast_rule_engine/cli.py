import ast
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Callable, List, NoReturn, Pattern

import yaml

from ast_rule_engine.parse import parse
from ast_rule_engine.patch_const import LegacyConstantRewriter


@dataclass(frozen=True)
class Options:
    spec_path: Path
    root_dir: Path
    inclue_glob: str
    select: Pattern[str]
    unselect: Pattern[str]
    exclude_pattern: Pattern[str]


def _dummy_get_ffi(_key: str) -> NoReturn:
    raise NotImplementedError("FFI is not supported yet")


class _NodeCollector(ast.NodeVisitor):
    def __init__(self, callback: Callable[[ast.AST], None]) -> None:
        self._callback = callback

    def visit(self, node: ast.AST) -> None:
        self._callback(node)
        super().visit(node)


def _get_all_nodes(node: ast.AST) -> List[ast.AST]:
    LegacyConstantRewriter().visit(node)
    nodes: List[ast.AST] = []
    _NodeCollector(nodes.append).visit(node)
    return nodes


def run_cli(options: Options) -> None:
    raw_spec = yaml.safe_load(options.spec_path.read_text("utf-8"))

    patterns = parse(raw_spec, _dummy_get_ffi)
    patterns = {
        name: pattern
        for name, pattern in patterns.items()
        if options.select.fullmatch(name) and not options.unselect.fullmatch(name)
    }

    root = options.root_dir.expanduser()
    path_to_nodes = {
        path: _get_all_nodes(ast.parse(path.read_text("utf-8")))
        for path in root.glob(options.inclue_glob)
        if not options.exclude_pattern.fullmatch(str(path)) and path.is_file()
    }

    for pattern_name, pattern in patterns.items():
        pattern_printed = False
        for path, nodes in path_to_nodes.items():
            path_printed = False
            for node in nodes:
                captures = pattern.match(node)
                if isinstance(captures, str):
                    continue

                if not pattern_printed:
                    print(f"Matches for {pattern_name!r}:")
                    pattern_printed = True

                if not path_printed:
                    print(f"  In {path}:")
                    path_printed = True

                print(
                    f"    at line {node.lineno}, col {node.col_offset}: {type(node).__name__}"
                )
                if captures:
                    for k, v in captures.items():
                        print(f"      - {k}: {v}")
