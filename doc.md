Patterns:

```

Root = {
    "stmt_rules": {
        ($name < string): Rule,
    },
}

Rule
    = Is-Rule
    | Or-Rule
    | And-Rule
    | Not-Rule
    | Ref-Rule
    | Var-Rule
    | Box-Rule
    | FFI-Rule

Is-Rule
    = { ("is(" . ($cls < ast-class) . ")"): { ($name < cls.attrs): Rule} | None }
    | "is(" . ($cls < ast-class) . ")"

Or-Rule = { ":or": List[Rule] }

And-Rule = { ":and": List[Rule] }

Not-Rule = { ":not": Rule } | "not(" . ($rule < Rule) . ")"

Ref-Rule = "~" . $rule-name

Var-Rule = "$" . $name

Box-Rule = "=" . Box-Value
    where (
        Box-Value
            = "True"
            | "False"
            | "None"
            | "..."
            | "str"
            | "int"
            | "float"
            | "bool"
            | python-string
            | /[0-9]+/
            | /[0-9+]\.[0-9+]/
    )

FFI-Rule
    = { "ffi(" . $func-name  . ")": ??? }
    | "ffi(" . $func-name  . ")"

```