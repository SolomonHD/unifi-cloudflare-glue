# OpenSpec Change Prompt

## Context
The unifi-cloudflare-glue Dagger module has a Python syntax error that prevents it from loading. When running any Dagger command with the module (e.g., `dagger call -m unifi-cloudflare-glue generate-cloudflare-config --source=./kcl`), the module fails with:
```
SyntaxError: f-string expression part cannot include a backslash (backend_config.py, line 42)
```

## Goal
Fix the Python syntax error in backend_config.py line 42 that prevents the Dagger module from loading.

## Scope

**In scope:**
- Fix the f-string syntax error in `src/main/backend_config.py` line 42

**Out of scope:**
- Any other changes to the module

## The Problem
Line 42 currently contains:
```python
return f"{{\n{',\n'.join(items)}\n{indent}}}"
```

Python f-strings cannot have backslashes inside the expression part (inside `{}`). The `\n` and the join with `,\n` are causing the syntax error.

## The Fix
Extract the newlines and join separator outside the f-string expression. The corrected code should be:
```python
return f"{{\n" + ",\n".join(items) + "\n{indent}}}"
```

Or alternatively:
```python
separator = ",\n"
return f"{{\n{separator.join(items)}\n{indent}}}"
```

## Acceptance Criteria
- [ ] Fix the syntax error in line 42
- [ ] Run `dagger call -m unifi-cloudflare-glue generate-cloudflare-config --source=./kcl` and verify it loads successfully
