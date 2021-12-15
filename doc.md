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
    | Forall-Rule
    | Exists-Rule
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

Forall-Rule = { ":forall": Rule }

Exists-Rule = { ":exists": Rule }

Ref-Rule = "~" . $rule-name

Var-Rule = "$" . $name

Box-Rule = Inline-Box-Rule | Tuple-Box-Rule
    where (
        Tuple-Box-Rule = {"=": List[Rule]} | {"=": List[Rule] + ["..."]}
        Inline-Box-Rule = "=" . Box-Value
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