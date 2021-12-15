from typing import Any, Callable
import yaml
from ast_rule_engine.draft import AndRule, BoxTypeRule, BoxValueRule, IsRule, NotRule, OrRule, RefRule, TupleRule
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
        is(Constant):
          value:
            ~truthy-value

  equals-with-None:
    :or:
      - is(Compare):
          ops:
            =: [is(Eq)]
          left:
            is(Constant):
              value: =None
      - is(Compare):
          ops:
            =: [is(Eq)]
          right:
            =:
              - is(Constant):
                  value: =None

  equals-with-None-2:
    :and:
      - is(Compare):
          ops:
            =: [is(Eq)]
      - :or:
        - is(Compare):
            left:
              is(Constant):
                value: =None
        - is(Compare):
            right:
              =:
                - is(Constant):
                    value: =None
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
                "Constant",
                {
                    "value": RefRule(
                        "truthy-value",
                        equals_if(lambda get_name: get_name("truthy-value") == parsed["truthy-value"])
                    ),
                }
            )
        }
    )


def test_equals_with_none_basic():
    parsed = parse(SOURCE, {}.__getitem__)
    assert parsed["equals-with-None"] == OrRule([
        IsRule("Compare", {
            "ops": TupleRule([
                IsRule("Eq", {}),
            ]),
            "left": IsRule("Constant", {"value": BoxValueRule(None)}),
        }),
        IsRule("Compare", {
            "ops": TupleRule([
                IsRule("Eq", {}),
            ]),
            "right": TupleRule([
                IsRule("Constant", {"value": BoxValueRule(None)}),
            ]),
        }),
    ])


def test_equals_with_none_DRY():
    parsed = parse(SOURCE, {}.__getitem__)
    assert parsed["equals-with-None-2"] == AndRule([
        IsRule("Compare", {
            "ops": TupleRule([
                IsRule("Eq", {}),
            ]),
        }),
        OrRule([
            IsRule("Compare", {
                "left": IsRule("Constant", {"value": BoxValueRule(None)}),
            }),
            IsRule("Compare", {
                "right": TupleRule([IsRule("Constant", {"value": BoxValueRule(None)})]),
            }),
        ]),
    ])

