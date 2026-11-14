"""Pure, in-memory backend conversion for a caller-owned secret execution path.

Returned HCL is still sensitive. Callers must keep it on protected channels;
this module never reads or writes files, logs content, or selects another backend.
"""

import math
import re
from typing import Literal

import hcl2
import yaml
from hcl2.utils import SerializationOptions
from lark.exceptions import LarkError


class BackendConfigError(ValueError):
    """Invalid backend input, with a diagnostic safe to show without its content."""


class _BackendLoader(yaml.SafeLoader):
    """Reject duplicate keys instead of silently changing backend identity."""

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            _validate_key(key)
            if key in result:
                raise BackendConfigError("Backend configuration has duplicate YAML keys")
            result[key] = self.construct_object(value_node, deep=deep)
        return result


def _validate_key(key) -> None:
    if not isinstance(key, str) or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_-]*", key) is None:
        raise BackendConfigError("Backend configuration has an invalid mapping key")


def _yaml_to_hcl_value(value, indent_level: int = 0) -> str:
    """Serialize only strings, booleans, finite numbers, lists and identifier maps.

    A depth bound rejects recursive YAML aliases and excessively nested input.
    No error includes keys, values, type representations, or parser snippets.
    """
    if indent_level > 64:
        raise BackendConfigError("Backend configuration exceeds the nesting limit")
    if isinstance(value, str):
        escapes = {"\\": "\\\\", '"': '\\"', "\n": "\\n", "\r": "\\r", "\t": "\\t"}
        parts = []
        for char in value:
            code = ord(char)
            if 0xD800 <= code <= 0xDFFF:
                raise BackendConfigError("Backend configuration contains invalid Unicode")
            parts.append(escapes.get(char, f"\\u{code:04x}" if code < 32 else char))
        # HCL quoted strings are templates, even inside lists and objects.
        escaped = "".join(parts).replace("${", "$${").replace("%{", "%%{")
        return f'"{escaped}"'
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        try:
            return str(value)
        except ValueError:
            raise BackendConfigError(
                "Backend configuration integer exceeds the size limit"
            ) from None
    if isinstance(value, float):
        if not math.isfinite(value):
            raise BackendConfigError("Backend configuration requires finite numbers")
        return repr(value)
    if isinstance(value, list):
        items = [_yaml_to_hcl_value(item, indent_level + 1) for item in value]
        return f'[{", ".join(items)}]'
    if isinstance(value, dict):
        if not value:
            return "{}"
        indent = "  " * indent_level
        inner_indent = "  " * (indent_level + 1)
        items = []
        for key, item in value.items():
            _validate_key(key)
            items.append(f"{inner_indent}{key} = {_yaml_to_hcl_value(item, indent_level + 1)}")
        return "{\n" + ",\n".join(items) + f"\n{indent}}}"
    if value is None:
        raise BackendConfigError("Backend configuration does not support null values")
    raise BackendConfigError("Backend configuration contains an unsupported value type")


def yaml_to_hcl(yaml_content: str) -> str:
    """Convert a nonempty YAML mapping to literal HCL, failing closed.

    YAML timestamps, binary/set tags, nulls, duplicate/invalid keys, recursive
    aliases and non-finite numbers are not part of the supported value contract.
    """
    if not isinstance(yaml_content, str):
        raise BackendConfigError("Backend configuration content must be text")
    try:
        yaml_data = yaml.load(yaml_content, Loader=_BackendLoader)
    except yaml.YAMLError:
        raise BackendConfigError("Backend configuration has invalid YAML syntax") from None
    except (RecursionError, ValueError) as error:
        if isinstance(error, BackendConfigError):
            raise
        raise BackendConfigError("Backend configuration exceeds YAML parsing limits") from None
    if yaml_data is None or yaml_data == {}:
        raise BackendConfigError("Backend configuration must not be empty")
    if not isinstance(yaml_data, dict):
        raise BackendConfigError("Backend configuration YAML must be a mapping")
    lines = []
    for key, value in yaml_data.items():
        _validate_key(key)
        lines.append(f"{key} = {_yaml_to_hcl_value(value)}")
    return "\n".join(lines)


def process_backend_config_content(content: str, format: Literal["yaml", "hcl"]) -> tuple[str, str]:
    """Validate the explicitly selected format and return sensitive HCL + suffix.

    HCL is syntax-checked, not evaluated, and preserved byte-for-byte. Terraform
    initialization remains responsible for backend-specific schema validation.
    Malformed YAML is never reinterpreted as HCL; there is no default format.
    """
    if not isinstance(content, str):
        raise BackendConfigError("Backend configuration content must be text")
    if format == "yaml":
        return yaml_to_hcl(content), ".tfbackend"
    if format != "hcl":
        raise BackendConfigError("Backend configuration format must be yaml or hcl")
    try:
        parsed = hcl2.loads(
            content,
            serialization_options=SerializationOptions(
                with_comments=False, preserve_scientific_notation=False
            ),
        )
    except (LarkError, ValueError):
        raise BackendConfigError("Backend configuration has invalid HCL syntax") from None
    except RecursionError:
        raise BackendConfigError("Backend configuration exceeds HCL parsing limits") from None
    if not parsed:
        raise BackendConfigError("Backend configuration must not be empty")
    pending = [(parsed, 0)]
    while pending:
        value, depth = pending.pop()
        if depth > 64:
            raise BackendConfigError("Backend configuration exceeds the nesting limit")
        if value is None:
            raise BackendConfigError("Backend configuration does not support null values")
        if isinstance(value, float) and not math.isfinite(value):
            raise BackendConfigError("Backend configuration requires finite numbers")
        if isinstance(value, dict):
            pending.extend((item, depth + 1) for item in value.values())
        elif isinstance(value, list):
            pending.extend((item, depth + 1) for item in value)
    return content, ".tfbackend"
