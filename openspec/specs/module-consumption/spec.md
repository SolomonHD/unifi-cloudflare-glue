# module-consumption Specification

## Purpose

Define requirements for documenting how external Terraform projects can consume the unifi-cloudflare-glue Terraform modules using Git-based module sourcing with version pinning.

## ADDED Requirements

### Requirement: Main README Module Consumption Section

The main [`README.md`](../../README.md) SHALL include a dedicated section explaining how to consume the Terraform modules from external projects.

#### Scenario: User discovers how to consume modules in their own project
Given: A user reading the main README
When: They want to use the modules in their own Terraform project
Then: They find a "Using as Terraform Modules" section after the "Modules" heading
And: The section explains Git-based module sourcing
And: Examples use the real GitHub URL `github.com/SolomonHD/unifi-cloudflare-glue`
And: Version pinning syntax `?ref=v0.1.0` is demonstrated
And: Both modules (unifi-dns and cloudflare-tunnel) are documented
And: Complete working examples with all required variables are provided

#### Scenario: Understanding Git-based module source syntax
Given: The "Using as Terraform Modules" section
When: A user needs to reference a specific version
Then: They see the double-slash syntax for subdirectories: `//terraform/modules/unifi-dns`
And: They see the version reference syntax: `?ref=v0.1.0`
And: They understand the full pattern: `github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/{module-name}?ref={version}`

#### Scenario: Complete unifi-dns module example
Given: The main README module consumption section
When: A user wants to use the unifi-dns module
Then: They find a complete example showing:
```hcl
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"

  config = {
    devices = [
      {
        friendly_hostname = "media-server"
        domain            = "internal.lan"
        nics = [
          {
            mac_address = "aa:bb:cc:dd:ee:01"
          }
        ]
      }
    ]
    default_domain = "internal.lan"
    site           = "default"
  }

  strict_mode = false
}
```

#### Scenario: Complete cloudflare-tunnel module example
Given: The main README module consumption section
When: A user wants to use the cloudflare-tunnel module
Then: They find a complete example showing:
```hcl
module "cloudflare_tunnel" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/cloudflare-tunnel?ref=v0.1.0"

  config = {
    zone_name  = "example.com"
    account_id = "your-cloudflare-account-id"
    tunnels = {
      "aa:bb:cc:dd:ee:ff" = {
        tunnel_name = "home-server"
        mac_address = "aa:bb:cc:dd:ee:ff"
        services = [
          {
            public_hostname   = "media.example.com"
            local_service_url = "http://jellyfin.internal.lan:8096"
            no_tls_verify     = false
          }
        ]
      }
    }
  }
}
```

### Requirement: Module README Git Source Examples

Each Terraform module README SHALL include examples of both local path and Git-based source patterns.

#### Scenario: unifi-dns README shows both source patterns
Given: The [`terraform/modules/unifi-dns/README.md`](../../../terraform/modules/unifi-dns/README.md)
When: A user reads the Usage section
Then: They see a local path example with comment:
```hcl
# Local path (for development within this repo)
module "unifi_dns" {
  source = "./terraform/modules/unifi-dns"
  # ... config
}
```
And: They see a Git source example with comment:
```hcl
# Git source (for consuming from external projects)
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"
  # ... config
}
```

#### Scenario: cloudflare-tunnel README shows both source patterns
Given: The [`terraform/modules/cloudflare-tunnel/README.md`](../../../terraform/modules/cloudflare-tunnel/README.md)
When: A user reads the Usage section
Then: They see a local path example with comment:
```hcl
# Local path (for development within this repo)
module "cloudflare_tunnel" {
  source = "./terraform/modules/cloudflare-tunnel"
  # ... config
}
```
And: They see a Git source example with comment:
```hcl
# Git source (for consuming from external projects)
module "cloudflare_tunnel" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/cloudflare-tunnel?ref=v0.1.0"
  # ... config
}
```

### Requirement: No Placeholder URLs

All documentation SHALL use the real GitHub repository URL without placeholders.

#### Scenario: Real GitHub URL used consistently
Given: Documentation files are updated with module source examples
When: The documentation is reviewed
Then: All module source references use `github.com/SolomonHD/unifi-cloudflare-glue`
And: No placeholder URLs like `github.com/yourorg/repo` remain
And: No placeholder URLs like `github.com/yourusername/unifi-cloudflare-glue` remain
And: The repository URL matches the actual GitHub repository

#### Scenario: Version references use v-prefix
Given: Version pinning examples in documentation
When: A user views the `?ref=` syntax
Then: All examples use the `v` prefix: `?ref=v0.1.0`
And: The version matches the current VERSION file (0.1.0)
And: The pattern follows Dagger/Git tag conventions

### Requirement: Required Variables Documented

Module consumption examples SHALL include all required variables with realistic values.

#### Scenario: unifi-dns example has all required fields
Given: The main README unifi-dns module example
When: A user copies the example
Then: The example includes:
- `config.devices` with at least one device
- `config.devices[].friendly_hostname`
- `config.devices[].nics` with at least one NIC
- `config.devices[].nics[].mac_address`
- `config.default_domain`
And: Optional `strict_mode` is shown with recommended default

#### Scenario: cloudflare-tunnel example has all required fields
Given: The main README cloudflare-tunnel module example
When: A user copies the example
Then: The example includes:
- `config.zone_name`
- `config.account_id`
- `config.tunnels` with at least one tunnel
- `config.tunnels[mac].tunnel_name`
- `config.tunnels[mac].mac_address`
- `config.tunnels[mac].services` with at least one service
- `config.tunnels[mac].services[].public_hostname`
- `config.tunnels[mac].services[].local_service_url`

### Requirement: Documentation Style Consistency

Module consumption documentation SHALL maintain consistency with existing documentation style and formatting.

#### Scenario: Markdown formatting matches existing style
Given: New documentation sections are added
When: The files are reviewed
Then: Headings follow existing hierarchy (##, ###)
And: Code blocks use proper syntax highlighting (```hcl)
And: Lists and tables match existing formatting
And: Line length and wrapping follow project conventions

#### Scenario: Technical terminology is consistent
Given: Module consumption documentation
When: Technical terms are used
Then: "Git-based module sourcing" is used consistently
And: "Version pinning" terminology matches existing docs
And: Module names match dagger.json and other references
And: Provider names and versions match existing documentation
