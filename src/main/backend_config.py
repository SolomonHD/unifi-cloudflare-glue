"""Backend configuration utilities for YAML to HCL conversion.

This module provides functions for converting YAML backend configuration files
to Terraform-compatible HCL format, enabling seamless integration with secret
management tools like vals.
"""

import yaml
from typing import Optional


def _yaml_to_hcl_value(value, indent_level: int = 0) -> str:
    """
    Recursively convert a Python value to HCL format.
    
    Args:
        value: The value to convert (str, int, float, bool, list, dict)
        indent_level: Current indentation level for nested structures
        
    Returns:
        String representation of the value in HCL format
    """
    if isinstance(value, str):
        # Escape quotes in strings
        escaped = value.replace('"', '\\"')
        return f'"{escaped}"'
    elif isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, (int, float)):
        return str(value)
    elif isinstance(value, list):
        if not value:
            return "[]"
        items = [_yaml_to_hcl_value(item, indent_level) for item in value]
        return f'[{", ".join(items)}]'
    elif isinstance(value, dict):
        if not value:
            return "{}"
        indent = "  " * indent_level
        inner_indent = "  " * (indent_level + 1)
        items = [f'{inner_indent}{k} = {_yaml_to_hcl_value(v, indent_level + 1)}' for k, v in value.items()]
        return f"{{\n" + ",\n".join(items) + "\n{indent}}}"
    else:
        # For unknown types, convert to string with quotes
        return f'"{str(value)}"'


def yaml_to_hcl(yaml_content: str) -> str:
    """
    Convert YAML content to HCL format.
    
    Args:
        yaml_content: String containing YAML data
        
    Returns:
        String containing HCL-formatted data
        
    Raises:
        yaml.YAMLError: If the content is not valid YAML
    """
    yaml_data = yaml.safe_load(yaml_content)
    
    if yaml_data is None:
        return ""
    
    if not isinstance(yaml_data, dict):
        raise ValueError("YAML content must be a dictionary (mapping)")
    
    hcl_lines = []
    for key, value in yaml_data.items():
        hcl_value = _yaml_to_hcl_value(value)
        hcl_lines.append(f'{key} = {hcl_value}')
    
    return '\n'.join(hcl_lines)


def process_backend_config_content(content: str) -> tuple[str, str]:
    """
    Process backend configuration content, converting YAML to HCL if necessary.
    
    Args:
        content: String containing backend configuration (YAML or HCL)
        
    Returns:
        Tuple of (content, extension) where content is the HCL-formatted backend config
        and extension is '.tfbackend' for mounting
    """
    # Try to parse as YAML
    try:
        yaml_data = yaml.safe_load(content)
        
        # If parsing succeeds and we got a dict, convert to HCL
        if isinstance(yaml_data, dict):
            hcl_content = yaml_to_hcl(content)
            return (hcl_content, '.tfbackend')
        elif yaml_data is None:
            # Empty YAML file, treat as HCL (pass through)
            return (content, '.tfbackend')
        else:
            # YAML parsed but not a dict (unexpected), treat as HCL
            return (content, '.tfbackend')
    except yaml.YAMLError:
        # Not valid YAML, treat as HCL (pass through)
        return (content, '.tfbackend')
