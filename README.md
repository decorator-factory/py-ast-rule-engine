# `py-ast-rule-engine`

This library provides a DSL (domain-specific language)
to match a pattern inside a Python AST (abstract syntax tree).

The library is currently at a draft stage: it sorta works.

## Why would you use this (in theory)?

- You want to write a plugin for `flake8` (or other linter)
- You want to write an AST optimizer
- You want to search for a pattern in a big codebase
- You want to search and replace a pattern (WIP)


## Brief example
```yaml
str-format:
  is(Call):
    func:
      is(Attribute):
        value:
          is(Constant):
            value:
              =str
        attr:
          ="format"

f-string:
  is(JoinedStr)

Assert-With-Format:
  is(Assert):
    test:
      ~str-format

Assert-With-F-String:
  is(Assert):
    test:
      ~f-string

Concatenating-2-F-Strings:
  is(BinOp):
    left:
      ~f-string
    right:
      ~f-string
    op:
      is(Add)

Concatenating-F-Strings:
  is(BinOp):
    left:
      :or:
        - ~f-string
        - ~Concatenating-F-Strings
    right:
      :or:
        - ~f-string
        - ~Concatenating-F-Strings
    op:
      is(Add)
```
