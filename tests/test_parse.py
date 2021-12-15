from typing import Any, Callable
import yaml
from ast_rule_engine.draft import AndRule, BoxTypeRule, BoxValueRule, IsRule, NotRule, OrRule, RefRule
from ast_rule_engine.parse import parse



class _EqualsIf:
    def __init__(self, predicate):
        self.predicate = predicate

    def __eq__(self, other):
        return self.predicate(other)

def equals_if(predicate: Callable[[Any], bool]) -> Any:
    return _EqualsIf(predicate)


SOURCE = yaml.safe_load(r"""
stmt-rules:
  truthy-value:
    :or:
      - =True
      - =...
      - :and: [=int, not(=0)]

  f-string:
    is(JoinedStr)

  ULA001: # `assert True`
    is(Assert):
      test:
        is(Const):
          value:
            ~truthy-value
""")


def test_truthy_value():
    parsed = parse(SOURCE, {}.__getitem__)
    assert parsed["truthy-value"] == OrRule([
        BoxValueRule(True),
        BoxValueRule(...),
        AndRule([BoxTypeRule(int), NotRule(BoxValueRule(0))]),
    ])


def test_f_string():
    parsed = parse(SOURCE, {}.__getitem__)
    assert parsed["f-string"] == IsRule("JoinedStr", {})


def test_ula_001():
    parsed = parse(SOURCE, {}.__getitem__)
    assert parsed["ULA001"] == IsRule(
        "Assert",
        {
            "test": IsRule(
                "Const",
                {
                    "value": RefRule(
                        "truthy-value",
                        equals_if(lambda get_name: get_name("truthy-value") == parsed["truthy-value"])
                    ),
                }
            )
        }
    )
