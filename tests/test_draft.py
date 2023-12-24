import ast
from ast_rule_engine.draft import IsRule
from ast_rule_engine.patch_const import LegacyConstantRewriter


def parse(code: str) -> ast.Module:
    tree = ast.parse(code)
    LegacyConstantRewriter().visit(tree)
    return tree


def test_is_rule():
    pat = IsRule("Assert", {"test": IsRule("Constant", {})})
    stmt = parse("assert 42").body[0]

    assert pat.match(stmt) == {}
