"""Unit tests for YAML to HCL backend config conversion."""

import pytest
import yaml
import sys
import os
import importlib.util

# Load backend_config.py directly without going through the package __init__.py
backend_config_path = os.path.join(
    os.path.dirname(__file__), '..', '..', 'src', 'main', 'backend_config.py'
)
spec = importlib.util.spec_from_file_location("backend_config", backend_config_path)
backend_config = importlib.util.module_from_spec(spec)
sys.modules["backend_config"] = backend_config
spec.loader.exec_module(backend_config)

# Now import the functions
_yaml_to_hcl_value = backend_config._yaml_to_hcl_value
yaml_to_hcl = backend_config.yaml_to_hcl
process_backend_config_content = backend_config.process_backend_config_content


class TestYamlToHclValue:
    """Test cases for _yaml_to_hcl_value function."""

    def test_string_conversion(self):
        """Test string value conversion with proper quoting."""
        assert _yaml_to_hcl_value("hello") == '"hello"'
        assert _yaml_to_hcl_value("my-bucket") == '"my-bucket"'

    def test_string_with_quotes(self):
        """Test string with quotes is properly escaped."""
        assert _yaml_to_hcl_value('say "hello"') == '"say \\"hello\\""'

    def test_integer_conversion(self):
        """Test integer conversion without quotes."""
        assert _yaml_to_hcl_value(42) == "42"
        assert _yaml_to_hcl_value(0) == "0"
        assert _yaml_to_hcl_value(-5) == "-5"

    def test_float_conversion(self):
        """Test float conversion without quotes."""
        assert _yaml_to_hcl_value(3.14) == "3.14"
        assert _yaml_to_hcl_value(0.0) == "0.0"
        assert _yaml_to_hcl_value(-2.5) == "-2.5"

    def test_boolean_conversion(self):
        """Test boolean conversion to lowercase true/false."""
        assert _yaml_to_hcl_value(True) == "true"
        assert _yaml_to_hcl_value(False) == "false"

    def test_list_conversion(self):
        """Test list conversion with HCL list syntax."""
        assert _yaml_to_hcl_value(["a", "b", "c"]) == '["a", "b", "c"]'
        assert _yaml_to_hcl_value([1, 2, 3]) == "[1, 2, 3]"
        assert _yaml_to_hcl_value([]) == "[]"

    def test_nested_list_conversion(self):
        """Test nested list conversion."""
        result = _yaml_to_hcl_value([["a", "b"], ["c", "d"]])
        assert result == '[["a", "b"], ["c", "d"]]'

    def test_dict_conversion(self):
        """Test dict/object conversion with HCL object syntax."""
        result = _yaml_to_hcl_value({"name": "dev"})
        assert 'name = "dev"' in result
        assert result.startswith("{")
        assert result.endswith("}")

    def test_empty_dict(self):
        """Test empty dict conversion."""
        assert _yaml_to_hcl_value({}) == "{}"

    def test_nested_dict_conversion(self):
        """Test deeply nested dict conversion."""
        data = {"level1": {"level2": {"level3": "value"}}}
        result = _yaml_to_hcl_value(data)
        assert "level1 =" in result
        assert "level2 =" in result
        assert "level3 =" in result
        assert '"value"' in result

    def test_complex_nested_structure(self):
        """Test complex nested structure with mixed types."""
        data = {
            "bucket": "my-bucket",
            "tags": ["env:prod", "team:platform"],
            "config": {
                "enabled": True,
                "count": 5,
                "nested": {
                    "value": 3.14
                }
            }
        }
        result = _yaml_to_hcl_value(data)
        # Check all values are present
        assert "bucket" in result
        assert "tags" in result
        assert "config" in result
        assert "enabled = true" in result
        assert "count = 5" in result

    def test_unknown_type_fallback(self):
        """Test that unknown types are converted to string."""
        # Test with None (should be quoted string)
        result = _yaml_to_hcl_value(None)
        assert result == '"None"'


class TestYamlToHcl:
    """Test cases for yaml_to_hcl function."""

    def test_simple_yaml_to_hcl(self):
        """Test simple YAML to HCL conversion."""
        yaml_content = """
bucket: my-bucket
key: path/to/state
region: us-east-1
"""
        result = yaml_to_hcl(yaml_content)
        assert "bucket = \"my-bucket\"" in result
        assert "key = \"path/to/state\"" in result
        assert "region = \"us-east-1\"" in result

    def test_yaml_with_booleans(self):
        """Test YAML with boolean values."""
        yaml_content = """
encrypt: true
versioning: false
"""
        result = yaml_to_hcl(yaml_content)
        assert "encrypt = true" in result
        assert "versioning = false" in result

    def test_yaml_with_numbers(self):
        """Test YAML with numeric values."""
        yaml_content = """
port: 8080
version: 1.5
"""
        result = yaml_to_hcl(yaml_content)
        assert "port = 8080" in result
        assert "version = 1.5" in result

    def test_yaml_with_lists(self):
        """Test YAML with list values."""
        yaml_content = """
tags:
  - env:prod
  - team:platform
"""
        result = yaml_to_hcl(yaml_content)
        assert "tags =" in result
        assert '"env:prod"' in result
        assert '"team:platform"' in result

    def test_empty_yaml(self):
        """Test empty YAML content."""
        result = yaml_to_hcl("")
        assert result == ""

    def test_yaml_with_nested_objects(self):
        """Test YAML with nested object values."""
        yaml_content = """
workspaces:
  name: dev
  tags:
    - env:dev
"""
        result = yaml_to_hcl(yaml_content)
        assert "workspaces =" in result
        assert "name = \"dev\"" in result
        assert "tags =" in result


class TestProcessBackendConfigContent:
    """Test cases for process_backend_config_content function."""

    def test_yaml_s3_backend(self):
        """Test S3 backend YAML conversion."""
        yaml_content = """
bucket: my-terraform-state-bucket
key: unifi-cloudflare-glue/terraform.tfstate
region: us-east-1
encrypt: true
dynamodb_table: terraform-state-lock
"""
        content, ext = process_backend_config_content(yaml_content)

        assert ext == ".tfbackend"
        assert "bucket = \"my-terraform-state-bucket\"" in content
        assert "key = \"unifi-cloudflare-glue/terraform.tfstate\"" in content
        assert "region = \"us-east-1\"" in content
        assert "encrypt = true" in content
        assert "dynamodb_table = \"terraform-state-lock\"" in content

    def test_yaml_azurerm_backend(self):
        """Test Azure backend YAML conversion."""
        yaml_content = """
storage_account_name: myterraformstate
container_name: terraform-state
key: unifi-cloudflare-glue/terraform.tfstate
resource_group_name: my-resource-group
"""
        content, ext = process_backend_config_content(yaml_content)

        assert ext == ".tfbackend"
        assert "storage_account_name = \"myterraformstate\"" in content
        assert "container_name = \"terraform-state\"" in content

    def test_yaml_gcs_backend(self):
        """Test GCS backend YAML conversion."""
        yaml_content = """
bucket: my-terraform-state-bucket
prefix: unifi-cloudflare-glue/terraform
"""
        content, ext = process_backend_config_content(yaml_content)

        assert ext == ".tfbackend"
        assert "bucket = \"my-terraform-state-bucket\"" in content
        assert "prefix = \"unifi-cloudflare-glue/terraform\"" in content

    def test_hcl_fallback(self):
        """Test that HCL files are passed through unchanged."""
        hcl_content = """
bucket = "my-bucket"
key    = "path/to/state"
region = "us-east-1"
"""
        content, ext = process_backend_config_content(hcl_content)

        assert ext == ".tfbackend"
        # HCL should pass through (YAML parse will fail, so original content returned)
        assert content == hcl_content

    def test_empty_content(self):
        """Test handling of empty content."""
        content, ext = process_backend_config_content("")

        assert ext == ".tfbackend"
        assert content == ""

    def test_yaml_with_list_values(self):
        """Test YAML with list values."""
        yaml_content = """
bucket: my-bucket
endpoints:
  - https://s3.amazonaws.com
  - https://s3.us-east-1.amazonaws.com
"""
        content, ext = process_backend_config_content(yaml_content)

        assert ext == ".tfbackend"
        assert "bucket = \"my-bucket\"" in content
        assert "endpoints =" in content
        assert '"https://s3.amazonaws.com"' in content

    def test_yaml_with_nested_objects(self):
        """Test YAML with nested object values."""
        yaml_content = """
workspaces:
  name: dev
  tags:
    - env:dev
    - team:platform
"""
        content, ext = process_backend_config_content(yaml_content)

        assert ext == ".tfbackend"
        assert "workspaces =" in content
        assert "name = \"dev\"" in content
        assert "tags =" in content


class TestYamlBackendConfigFixtures:
    """Test fixtures for YAML backend configs."""

    def test_s3_yaml_fixture(self, tmp_path):
        """Create and validate S3 backend YAML fixture."""
        s3_yaml = {
            "bucket": "my-terraform-state-bucket",
            "key": "unifi-cloudflare-glue/terraform.tfstate",
            "region": "us-east-1",
            "encrypt": True,
            "dynamodb_table": "terraform-state-lock"
        }

        yaml_file = tmp_path / "s3-backend.yaml"
        yaml_file.write_text(yaml.dump(s3_yaml))

        # Verify YAML can be loaded
        loaded = yaml.safe_load(yaml_file.read_text())
        assert loaded["bucket"] == "my-terraform-state-bucket"
        assert loaded["encrypt"] is True

    def test_azurerm_yaml_fixture(self, tmp_path):
        """Create and validate Azure backend YAML fixture."""
        azurerm_yaml = {
            "storage_account_name": "myterraformstate",
            "container_name": "terraform-state",
            "key": "unifi-cloudflare-glue/terraform.tfstate",
            "resource_group_name": "my-resource-group"
        }

        yaml_file = tmp_path / "azurerm-backend.yaml"
        yaml_file.write_text(yaml.dump(azurerm_yaml))

        loaded = yaml.safe_load(yaml_file.read_text())
        assert loaded["storage_account_name"] == "myterraformstate"

    def test_gcs_yaml_fixture(self, tmp_path):
        """Create and validate GCS backend YAML fixture."""
        gcs_yaml = {
            "bucket": "my-terraform-state-bucket",
            "prefix": "unifi-cloudflare-glue/terraform"
        }

        yaml_file = tmp_path / "gcs-backend.yaml"
        yaml_file.write_text(yaml.dump(gcs_yaml))

        loaded = yaml.safe_load(yaml_file.read_text())
        assert loaded["bucket"] == "my-terraform-state-bucket"

    def test_remote_yaml_fixture(self, tmp_path):
        """Create and validate remote backend YAML fixture."""
        remote_yaml = {
            "organization": "my-organization",
            "workspaces": {
                "name": "unifi-cloudflare-glue"
            }
        }

        yaml_file = tmp_path / "remote-backend.yaml"
        yaml_file.write_text(yaml.dump(remote_yaml))

        loaded = yaml.safe_load(yaml_file.read_text())
        assert loaded["organization"] == "my-organization"
        assert loaded["workspaces"]["name"] == "unifi-cloudflare-glue"


class TestYamlToHclFormatting:
    """Test HCL formatting and alignment."""

    def test_key_value_formatting(self):
        """Test that key=value pairs are properly formatted."""
        result = _yaml_to_hcl_value({"bucket": "test"})
        assert "bucket = \"test\"" in result

    def test_multiple_keys(self):
        """Test formatting with multiple keys."""
        result = _yaml_to_hcl_value({
            "bucket": "my-bucket",
            "key": "my-key",
            "region": "us-east-1"
        })
        lines = result.strip().split("\n")
        # Check it's formatted as HCL object
        assert result.startswith("{")
        assert result.endswith("}")

    def test_generated_hcl_syntax(self):
        """Test that generated HCL is syntactically valid."""
        yaml_content = """
bucket: my-bucket
key: path/to/state
region: us-east-1
encrypt: true
"""
        content, _ = process_backend_config_content(yaml_content)

        # Basic syntax checks
        assert "=" in content  # Has key=value pairs
        assert content.count('"') % 2 == 0  # Quotes are balanced
        lines = [l.strip() for l in content.split("\n") if l.strip()]
        for line in lines:
            # Each non-empty line should have an equals sign (key = value)
            assert "=" in line
