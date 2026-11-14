"""Unit tests for YAML to HCL backend config conversion."""

import datetime
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import traceback

import hcl2
import pytest
import yaml

# Load backend_config.py directly without going through the package __init__.py
backend_config_path = os.path.join(
    os.path.dirname(__file__), "..", "..", "src", "main", "backend_config.py"
)
spec = importlib.util.spec_from_file_location("backend_config", backend_config_path)
backend_config = importlib.util.module_from_spec(spec)
sys.modules["backend_config"] = backend_config
spec.loader.exec_module(backend_config)

# Now import the functions
_yaml_to_hcl_value = backend_config._yaml_to_hcl_value
yaml_to_hcl = backend_config.yaml_to_hcl
process_backend_config_content = backend_config.process_backend_config_content
BackendConfigError = backend_config.BackendConfigError


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
            "config": {"enabled": True, "count": 5, "nested": {"value": 3.14}},
        }
        result = _yaml_to_hcl_value(data)
        # Check all values are present
        assert "bucket" in result
        assert "tags" in result
        assert "config" in result
        assert "enabled = true" in result
        assert "count = 5" in result

    @pytest.mark.parametrize(
        "value",
        [None, b"synthetic", {"synthetic"}, (1, 2), datetime.date(2026, 1, 1), object()],
    )
    def test_unknown_types_are_rejected(self, value):
        """Unsupported types are never silently stringified."""
        with pytest.raises(BackendConfigError, match="null values|unsupported value type"):
            _yaml_to_hcl_value(value)


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
        assert 'bucket = "my-bucket"' in result
        assert 'key = "path/to/state"' in result
        assert 'region = "us-east-1"' in result

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
        """An empty configuration cannot accidentally select local state."""
        with pytest.raises(BackendConfigError, match="must not be empty"):
            yaml_to_hcl("")

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
        assert 'name = "dev"' in result
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
        content, ext = process_backend_config_content(yaml_content, "yaml")

        assert ext == ".tfbackend"
        assert 'bucket = "my-terraform-state-bucket"' in content
        assert 'key = "unifi-cloudflare-glue/terraform.tfstate"' in content
        assert 'region = "us-east-1"' in content
        assert "encrypt = true" in content
        assert 'dynamodb_table = "terraform-state-lock"' in content

    def test_yaml_azurerm_backend(self):
        """Test Azure backend YAML conversion."""
        yaml_content = """
storage_account_name: myterraformstate
container_name: terraform-state
key: unifi-cloudflare-glue/terraform.tfstate
resource_group_name: my-resource-group
"""
        content, ext = process_backend_config_content(yaml_content, "yaml")

        assert ext == ".tfbackend"
        assert 'storage_account_name = "myterraformstate"' in content
        assert 'container_name = "terraform-state"' in content

    def test_yaml_gcs_backend(self):
        """Test GCS backend YAML conversion."""
        yaml_content = """
bucket: my-terraform-state-bucket
prefix: unifi-cloudflare-glue/terraform
"""
        content, ext = process_backend_config_content(yaml_content, "yaml")

        assert ext == ".tfbackend"
        assert 'bucket = "my-terraform-state-bucket"' in content
        assert 'prefix = "unifi-cloudflare-glue/terraform"' in content

    def test_explicit_hcl(self):
        """Explicit HCL is parsed and preserved without YAML detection."""
        hcl_content = """
bucket = "my-bucket"
key    = "path/to/state"
region = "us-east-1"
"""
        content, ext = process_backend_config_content(hcl_content, "hcl")

        assert ext == ".tfbackend"
        assert content == hcl_content

    @pytest.mark.parametrize("format", ["yaml", "hcl"])
    def test_empty_content(self, format):
        """Both explicit formats reject missing settings."""
        with pytest.raises(BackendConfigError, match="must not be empty"):
            process_backend_config_content("", format)

    def test_yaml_with_list_values(self):
        """Test YAML with list values."""
        yaml_content = """
bucket: my-bucket
endpoints:
  - https://s3.amazonaws.com
  - https://s3.us-east-1.amazonaws.com
"""
        content, ext = process_backend_config_content(yaml_content, "yaml")

        assert ext == ".tfbackend"
        assert 'bucket = "my-bucket"' in content
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
        content, ext = process_backend_config_content(yaml_content, "yaml")

        assert ext == ".tfbackend"
        assert "workspaces =" in content
        assert 'name = "dev"' in content
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
            "dynamodb_table": "terraform-state-lock",
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
            "resource_group_name": "my-resource-group",
        }

        yaml_file = tmp_path / "azurerm-backend.yaml"
        yaml_file.write_text(yaml.dump(azurerm_yaml))

        loaded = yaml.safe_load(yaml_file.read_text())
        assert loaded["storage_account_name"] == "myterraformstate"

    def test_gcs_yaml_fixture(self, tmp_path):
        """Create and validate GCS backend YAML fixture."""
        gcs_yaml = {
            "bucket": "my-terraform-state-bucket",
            "prefix": "unifi-cloudflare-glue/terraform",
        }

        yaml_file = tmp_path / "gcs-backend.yaml"
        yaml_file.write_text(yaml.dump(gcs_yaml))

        loaded = yaml.safe_load(yaml_file.read_text())
        assert loaded["bucket"] == "my-terraform-state-bucket"

    def test_remote_yaml_fixture(self, tmp_path):
        """Create and validate remote backend YAML fixture."""
        remote_yaml = {
            "organization": "my-organization",
            "workspaces": {"name": "unifi-cloudflare-glue"},
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
        assert 'bucket = "test"' in result

    def test_multiple_keys(self):
        """Test formatting with multiple keys."""
        result = _yaml_to_hcl_value({"bucket": "my-bucket", "key": "my-key", "region": "us-east-1"})
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
        content, _ = process_backend_config_content(yaml_content, "yaml")
        parsed = hcl2.loads(content)
        assert set(parsed) == {"bucket", "key", "region", "encrypt"}
        assert parsed["encrypt"] is True


class TestBackendValidation:
    @pytest.mark.parametrize("format", [None, "", "auto", "YAML", "json", "SYNTHETIC_CANARY"])
    def test_format_is_explicit_and_constrained(self, format):
        with pytest.raises(BackendConfigError, match="format must be yaml or hcl") as error:
            process_backend_config_content("bucket: synthetic", format)
        assert "SYNTHETIC_CANARY" not in str(error.value)

    def test_missing_format_is_a_signature_error(self):
        with pytest.raises(TypeError):
            process_backend_config_content("bucket: synthetic")

    @pytest.mark.parametrize("format", ["yaml", "hcl"])
    @pytest.mark.parametrize("content", [None, b"synthetic", {}, 42])
    def test_content_must_be_text(self, content, format):
        with pytest.raises(BackendConfigError, match="content must be text"):
            process_backend_config_content(content, format)

    @pytest.mark.parametrize("content", ["{}", "# synthetic comment", "---\n# comment", "null"])
    def test_empty_yaml_is_rejected(self, content):
        with pytest.raises(BackendConfigError, match="must not be empty"):
            process_backend_config_content(content, "yaml")

    @pytest.mark.parametrize("content", ["[]", "- synthetic", "synthetic", "42", "true"])
    def test_non_mapping_yaml_is_not_hcl(self, content):
        with pytest.raises(BackendConfigError, match="YAML must be a mapping"):
            process_backend_config_content(content, "yaml")

    @pytest.mark.parametrize(
        "content,category",
        [
            ("bucket: [SYNTHETIC_CANARY", "invalid YAML syntax"),
            ('bucket = "SYNTHETIC_CANARY"', "YAML must be a mapping"),
            ("bucket: !!python/object:SYNTHETIC_CANARY {}", "invalid YAML syntax"),
            ("bucket: synthetic\n---\nbucket: SYNTHETIC_CANARY", "invalid YAML syntax"),
            ("bucket: synthetic\nbucket: SYNTHETIC_CANARY", "duplicate YAML keys"),
            ("nested: {bucket: synthetic, bucket: SYNTHETIC_CANARY}", "duplicate YAML keys"),
            ("bucket: null\nother: SYNTHETIC_CANARY", "null values"),
            ("bucket: 2026-01-01\nother: SYNTHETIC_CANARY", "unsupported value type"),
            ("bucket: 2026-01-01T01:02:03Z\nother: SYNTHETIC_CANARY", "unsupported value type"),
            ("bucket: !!binary c3ludGhldGlj\nother: SYNTHETIC_CANARY", "unsupported value type"),
            ("bucket: !!set {synthetic: null}\nother: SYNTHETIC_CANARY", "unsupported value type"),
            ("bucket: .nan\nother: SYNTHETIC_CANARY", "finite numbers"),
            ("bucket: .inf\nother: SYNTHETIC_CANARY", "finite numbers"),
            ("bucket: -.inf\nother: SYNTHETIC_CANARY", "finite numbers"),
            ("bucket: &loop [*loop]\nother: SYNTHETIC_CANARY", "nesting limit"),
            ("SYNTHETIC_CANARY.bad: synthetic", "invalid mapping key"),
            ("nested: {SYNTHETIC_CANARY.bad: synthetic}", "invalid mapping key"),
            ("? [SYNTHETIC_CANARY]\n: synthetic", "invalid mapping key"),
        ],
    )
    def test_yaml_errors_keep_categories_not_content(self, content, category, capsys):
        with pytest.raises(BackendConfigError, match=category) as error:
            process_backend_config_content(content, "yaml")
        assert "SYNTHETIC_CANARY" not in str(error.value)
        assert "SYNTHETIC_CANARY" not in "".join(traceback.format_exception(error.value))
        captured = capsys.readouterr()
        assert captured.out == captured.err == ""

    @pytest.mark.parametrize(
        "content", ['bucket = ["SYNTHETIC_CANARY"', 'bucket: "SYNTHETIC_CANARY"']
    )
    def test_hcl_errors_are_sanitized(self, content, capsys):
        with pytest.raises(BackendConfigError, match="invalid HCL syntax") as error:
            process_backend_config_content(content, "hcl")
        assert "SYNTHETIC_CANARY" not in "".join(traceback.format_exception(error.value))
        captured = capsys.readouterr()
        assert captured.out == captured.err == ""

    def test_comments_only_hcl_is_empty(self):
        with pytest.raises(BackendConfigError, match="must not be empty"):
            process_backend_config_content("# comment\n/* comment */", "hcl")

    @pytest.mark.parametrize(
        "content,category",
        [
            ("bucket = null", "null values"),
            ("config = { values = [null] }", "null values"),
            ("value = 1e999", "finite numbers"),
            ("config = { value = -1e999 }", "finite numbers"),
        ],
    )
    def test_hcl_rejects_null_and_non_finite_values(self, content, category):
        with pytest.raises(BackendConfigError, match=category):
            process_backend_config_content(content, "hcl")

    def test_hcl_preserves_comments_heredoc_and_finite_exponents(self):
        content = "# synthetic\nbucket = <<EOF\nsynthetic\nEOF\nvalue = 1.0e-20\n"
        assert process_backend_config_content(content, "hcl") == (content, ".tfbackend")

    @pytest.mark.parametrize("key", ["", "bad.key", "bad key", 'bad"key', "1key", 1, True, None])
    def test_invalid_keys_are_rejected_at_every_depth(self, key):
        with pytest.raises(BackendConfigError, match="invalid mapping key"):
            _yaml_to_hcl_value({"nested": {key: "synthetic"}})

    @pytest.mark.parametrize("value", [float("nan"), float("inf"), -float("inf")])
    def test_non_finite_python_values_are_rejected(self, value):
        with pytest.raises(BackendConfigError, match="finite numbers"):
            _yaml_to_hcl_value(value)

    def test_invalid_unicode_is_rejected(self):
        with pytest.raises(BackendConfigError, match="invalid Unicode"):
            _yaml_to_hcl_value("synthetic\ud800")

    def test_mapping_alias_is_rejected_without_recursing_forever(self):
        with pytest.raises(BackendConfigError, match="nesting limit"):
            yaml_to_hcl("bucket: &loop {again: *loop}")

    def test_ordinary_alias_preserves_values(self):
        converted = yaml_to_hcl("bucket: &value synthetic\nkey: *value")
        assert converted == 'bucket = "synthetic"\nkey = "synthetic"'


class TestRealHclSemantics:
    @pytest.mark.parametrize(
        "value",
        [
            'say "hello" at C:\\synthetic\\state\nnext\rline\tend',
            "${synthetic.token} %{ if true }literal%{ endif } $${already} %%{already}",
            "\x00\x01\b\f\x1f snowman \u2603 smile \U0001f600",
            {"enabled": True, "count": -5, "ratio": 1e-20, "empty_map": {}, "empty_list": []},
            {"workspaces": {"name": "synthetic"}, "tags": ["a", {"key-name": [False, 0, 3.14]}]},
        ],
    )
    def test_terraform_evaluates_literal_values_exactly(self, value, tmp_path):
        """Terraform's own HCL parser/evaluator proves literal escaping, not quote counts."""
        terraform = shutil.which("terraform")
        if terraform is None:
            pytest.skip("Terraform parser/evaluator is not installed")
        expression = _yaml_to_hcl_value(value)
        # All inputs are synthetic. No backend, providers, or external credentials are used.
        formatted = subprocess.run(
            [terraform, "fmt", "-write=false", "-no-color", "-"],
            input=f"value = {expression}\n",
            text=True,
            capture_output=True,
            timeout=30,
            env={"PATH": os.environ["PATH"], "CHECKPOINT_DISABLE": "1"},
        )
        assert formatted.returncode == 0, formatted.stderr
        # Console reads one expression per line; literal newlines are already escaped.
        console_expression = expression.replace("\n", " ")
        result = subprocess.run(
            [terraform, "console", "-no-color"],
            input=f"jsonencode({console_expression})\n",
            text=True,
            capture_output=True,
            cwd=tmp_path,
            timeout=30,
            env={"PATH": os.environ["PATH"], "TF_IN_AUTOMATION": "1", "CHECKPOINT_DISABLE": "1"},
        )
        assert result.returncode == 0, result.stderr
        assert json.loads(json.loads(result.stdout)) == value

    def test_yaml_backend_identity_and_locking_parse(self):
        data = {
            "bucket": "synthetic-state",
            "key": "synthetic/terraform.tfstate",
            "region": "us-east-1",
            "workspace_key_prefix": "synthetic-workspaces",
            "encrypt": True,
            "use_lockfile": True,
            "endpoints": {"s3": "https://synthetic.invalid"},
        }
        hcl, suffix = process_backend_config_content(yaml.safe_dump(data), "yaml")
        from hcl2.utils import SerializationOptions

        assert (
            hcl2.loads(hcl, serialization_options=SerializationOptions(strip_string_quotes=True))
            == data
        )
        assert suffix == ".tfbackend"
        assert process_backend_config_content(hcl, "hcl") == (hcl, suffix)
