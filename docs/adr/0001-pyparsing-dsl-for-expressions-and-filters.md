# 1. Custom PyParsing DSL for Expressions and Filters

## Status
accepted

Report Designers need to define field calculation formulas and filter rules dynamically in the web editor without developer intervention. We chose custom domain-specific grammars built with PyParsing that compile down to Django ORM `Expression` and `Q` objects rather than evaluating Python code or exposing SQL. This provides an intuitive, CamelCase formula syntax for report designers while maintaining strict security guarantees against arbitrary code execution and SQL injection.

### Considered Options
- **Python `eval()` / `simpleeval`**: Rejected due to sandbox escape risks and mismatch with Django ORM aggregation semantics.
- **Django ORM JSON/Dict structures**: Rejected because internal ORM lookup syntax (`__`) is error-prone and hostile to non-developer users.
- **Raw SQL Snippets**: Rejected to maintain database portability and prevent SQL injection.

### Consequences
- Grammar rules and custom functions must be maintained in the parser definitions (`reportcraft.utils`).
- Expressions are constrained to supported AST nodes and explicitly mapped functions.
