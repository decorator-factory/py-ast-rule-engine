# `py-ast-rule-engine`

This library provides a DSL (domain-specific language)
to match a pattern inside a Python AST (abstract syntax tree).

The library is currently at a draft stage: it sorta works.

# CLI example

```bash
$ python -m ast_rule_engine samples/ --spec draft.yaml
Matches for 'ULA001':
  In samples/asserts_example0.py:
    at line 5, col 4: Assert
    at line 6, col 4: Assert
    at line 7, col 4: Assert
Matches for 'ULA002':
  In samples/asserts_example0.py:
    at line 8, col 4: Assert
Matches for 'ULA003':
  In samples/asserts_example0.py:
    at line 9, col 4: Assert
Matches for 'ULA004':
  In samples/asserts_example0.py:
    at line 10, col 4: Assert
Matches for 'ULA005':
  In samples/asserts_example0.py:
    at line 11, col 4: Assert
Matches for 'ULA006':
  In samples/asserts_example1.py:
    at line 5, col 4: Assert
    at line 8, col 4: Assert
    at line 9, col 4: Assert
    at line 10, col 4: Assert
```


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
