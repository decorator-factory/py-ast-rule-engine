import re
import ast
from dataclasses import dataclass
from typing import Callable, Dict

from ast_rule_engine.draft import (
    BoxTypeRule,
    BoxValueRule,
    FFIRule,
    IsRule,
    Match,
    NotRule,
    OrRule,
    AndRule,
    Pattern,
    RefRule,
    Term,
    VarRule,
)


@dataclass(frozen=True)
class ParseError(Exception):
    path: tuple
    message: str


GetPattern = Callable[[str], Pattern]
GetFFI = Callable[[str], Callable[[Term], Match]]


def parse(source: object, get_ffi: GetFFI) -> Dict[str, Pattern]:
    if not isinstance(source, dict):
        raise ParseError((), "Expected a dict")

    stmt_rules = source.get("stmt-rules")

    if not isinstance(stmt_rules, dict):
        raise ParseError((), "Expected a `stmt-rules` dict")

    for rule_name in stmt_rules.keys():
        if not isinstance(rule_name, str):
            raise ParseError((rule_name,), "Expected key to be a string")

    def look_up_rule(name: str, /) -> Pattern:
        return patterns[name]

    patterns = {}

    for rule_name, raw_rule in stmt_rules.items():
        pattern = parse_rule(raw_rule, (rule_name,), look_up_rule, get_ffi)
        patterns[rule_name] = pattern

    return patterns


def parse_rule(
    raw_rule: object,
    path: tuple,
    look_up_rule: Callable[[str], Pattern],
    get_ffi: GetFFI,
) -> Pattern:
    if isinstance(raw_rule, dict):
        if raw_rule == {}:
            raise ParseError(
                path,
                "Expected one of ':and', ':or', ':not', 'is(...)'. Got empty dict"
            )

        elif ":or" in raw_rule:
            variants = raw_rule[":or"]
            path += (":or",)
            if not isinstance(variants, list):
                raise ParseError(path, "Expected a list")
            return OrRule([
                parse_rule(raw_rule, path + (i,), look_up_rule, get_ffi)
                for i, raw_rule in enumerate(variants)
            ])

        elif ":and" in raw_rule:
            branches = raw_rule[":and"]
            path += (":and",)
            if not isinstance(branches, list):
                raise ParseError(path, "Expected a list")
            return AndRule([
                parse_rule(raw_rule, path + (i,), look_up_rule, get_ffi)
                for i, raw_rule in enumerate(branches)
            ])

        elif ":not" in raw_rule:
            raw_attrs = raw_rule[":not"]
            path += (":not",)
            return NotRule(parse_rule(raw_attrs, path, look_up_rule, get_ffi))

        elif all(isinstance(key, str) and key.startswith("is(") and key.endswith(")") for key in raw_rule.keys()):
            patterns = []

            for key, raw_attrs in raw_rule.items():
                if raw_attrs is None:
                    raw_attrs = {}

                if not isinstance(raw_attrs, dict):
                    raise ParseError(path + (key,), "Expected a dict")
                for attr in raw_attrs.keys():
                    if not isinstance(attr, str):
                        raise ParseError(path + (key, attr), "Expected a string key")
                attr_rules = {
                    attr: parse_rule(raw_subrule, path + (key, attr), look_up_rule, get_ffi)
                    for attr, raw_subrule in raw_attrs.items()
                }
                patterns.append(IsRule(key[3:-1], attr_rules))

            if len(patterns) == 1:
                return patterns[0]

            return OrRule(patterns)


        else:
            raise ParseError(
                path,
                "Expected one of ':and', ':or', ':not', 'is(...)'."
                "Got keys: {0!r}".format(set(raw_rule))
            )

    elif isinstance(raw_rule, str):
        if raw_rule == "":
            raise ParseError(path, "I don't understand an empty string")

        elif raw_rule.startswith("="):
            const = raw_rule[1:]
            if const == "True":
                return BoxValueRule(True)
            elif const == "False":
                return BoxValueRule(False)
            elif const == "None":
                return BoxValueRule(None)
            elif const == "...":
                return BoxValueRule(...)
            elif const == "int":
                return BoxTypeRule(int)
            elif const == "str":
                return BoxTypeRule(str)
            elif const == "bool":
                return BoxTypeRule(bool)
            elif const.startswith(('"', "'")):
                return BoxValueRule(ast.literal_eval(const))
            elif re.match(r"[0-9]+", const):
                return BoxValueRule(int(const))
            elif re.match(r"[0-9]+\.[0-9]+", const):
                return BoxValueRule(float(const))
            else:
                raise ParseError(path, "Unknown constant: {0!r}".format(const))

        elif raw_rule.startswith("not(") and raw_rule.endswith(")"):
            raw_negated = raw_rule[4:-1]
            return parse_rule({":not": raw_negated}, path, look_up_rule, get_ffi)

        elif raw_rule.startswith("is(") and raw_rule.endswith(")"):
            return parse_rule({raw_rule: None}, path, look_up_rule, get_ffi)

        elif raw_rule.startswith("ffi(") and raw_rule.endswith(")"):
            function_name = raw_rule[4:-1]
            return FFIRule(function_name, get_ffi)

        elif raw_rule.startswith("~"):
            return RefRule(raw_rule[1:], look_up_rule)

        elif raw_rule.startswith("$"):
            return VarRule(raw_rule[1:])

        else:
            raise ParseError(path, "Unknown rule: {0!r}".format(raw_rule))

    else:
        raise ParseError(path, "I don't understand this at all: {0!r}".format(raw_rule))

