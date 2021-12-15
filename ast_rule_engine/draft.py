from abc import ABC
import ast
from dataclasses import dataclass
from typing import Callable, Dict, List, Sequence, Union


@dataclass
class Box:
    value: object


Term = Union[ast.AST, List["Term"], Box]
Captures = Dict[str, Term]
Match = Union[Captures, str]


def to_term(obj: object) -> Term:
    if isinstance(obj, ast.AST):
        return obj
    elif isinstance(obj, (list, tuple)):
        return [to_term(x) for x in obj]
    else:
        return Box(obj)


class Pattern(ABC):
    def match(self, term: Term, /) -> Match:
        raise NotImplementedError


@dataclass(frozen=True)
class IsRule(Pattern):
    class_name: str
    attribute_rules: Dict[str, Pattern]

    def match(self, term: Term, /) -> Match:
        if not isinstance(term, ast.AST):
            return "Cannot match a {0}".format(self.class_name)

        node_cls = getattr(ast, self.class_name)
        if not isinstance(term, node_cls):
            return "{0} is not a {1}".format(type(term).__name__, self.class_name)

        captures = {}

        for name, pattern in self.attribute_rules.items():
            attr = to_term(getattr(term, name))
            submatch = pattern.match(attr)
            if isinstance(submatch, str):
                return "In attr {0}: {1}".format(attr, submatch)
            captures.update(submatch)

        return captures


@dataclass(frozen=True)
class OrRule(Pattern):
    patterns: Sequence[Pattern]

    def match(self, term: Term, /) -> Match:
        failed = []
        for pattern in self.patterns:
            match = pattern.match(term)
            if isinstance(match, str):
                failed.append(match)
            else:
                return match
        return "No patterns matched because: [{0}]".format(", ".join(failed))


@dataclass(frozen=True)
class AndRule(Pattern):
    patterns: Sequence

    def match(self, term: Term, /) -> Match:
        result = {}
        for pattern in self.patterns:
            match = pattern.match(term)
            if isinstance(match, str):
                return match
            result.update(match)
        return result


@dataclass(frozen=True)
class NotRule(Pattern):
    wrapped: Pattern

    def match(self, term: Term, /) -> Match:
        submatch = self.wrapped.match(term)
        if not isinstance(submatch, str) :
            return "Shouldn't have matched"
        return {}


@dataclass(frozen=True)
class RefRule(Pattern):
    name: str
    get_pattern: Callable[[str], Pattern]

    def match(self, term: Term, /) -> Match:
        pattern = self.get_pattern(self.name)
        return pattern.match(term)


@dataclass(frozen=True)
class VarRule(Pattern):
    name: str

    def match(self, term: Term, /) -> Match:
        return {self.name: term}


@dataclass(frozen=True)
class BoxTypeRule(Pattern):
    cls: type

    def match(self, term: Term, /) -> Match:
        if not isinstance(term, Box):
            return "Not a box"

        if not isinstance(term.value , self.cls):
            return "Expected a {0}, got {1}".format(
                self.cls.__name__,
                type(term.value).__name__,
            )

        return {}


@dataclass(frozen=True)
class BoxValueRule(Pattern):
    value: object

    def match(self, term: Term, /) -> Match:
        if not isinstance(term, Box):
            return "Not a box"

        if not isinstance(term.value , type(self.value)):
            return "Expected a {0}, got {1}".format(
                type(self.value).__name__,
                type(term.value).__name__,
            )

        if term.value != self.value:
            return "Expected {0!r}, got {1!r}".format(self.value, term.value)

        return {}


@dataclass(frozen=True)
class FFIRule(Pattern):
    name: str
    get_function: Callable[[str], Callable[[Term], Match]]

    def match(self, term: Term, /) -> Match:
        fn = self.get_function(self.name)
        return fn(term)


@dataclass(frozen=True)
class TupleRule(Pattern):
    patterns: Sequence[Pattern]

    def match(self, term: Term, /) -> Match:
        if not isinstance(term, list):
            return "Not a list"

        if len(term) != len(self.patterns):
            return "Pattern is {0} elements long, got {1}".format(
                len(self.patterns),
                len(term),
            )

        result = {}
        for i, (subterm, subpattern) in enumerate(zip(term, self.patterns)):
            match = subpattern.match(subterm)
            if isinstance(match, str):
                return "At pattern #{0}: {1}".format(i, match)
            result.update(match)
        return result


@dataclass(frozen=True)
class ForallRule(Pattern):
    predicate: Pattern

    def match(self, term: Term, /) -> Match:
        if not isinstance(term, list):
            return "Not a list"

        result = {}
        for i, subterm in enumerate(term):
            match  = self.predicate.match(subterm)
            if isinstance(match, str):
                return "At item #{0}: {1}".format(i, match)
            result.update(match)
        return result


@dataclass(frozen=True)
class ExistsRule(Pattern):
    predicate: Pattern

    def match(self, term: Term, /) -> Match:
        if not isinstance(term, list):
            return "Not a list"

        if not term:
            return "Empty list"

        errors = []
        for subterm in term:
            match  = self.predicate.match(subterm)
            if not isinstance(match, str):
                return match
            errors.append(match)
        return "; ".join(errors)
