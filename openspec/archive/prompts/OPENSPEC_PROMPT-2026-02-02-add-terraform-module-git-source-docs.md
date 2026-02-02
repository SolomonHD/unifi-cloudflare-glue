# OpenSpec Change Prompt

## Context

The `unifi-cloudflare-glue` repository contains two Terraform modules (`unifi-dns` and `cloudflare-tunnel`) that are designed to be consumed by external Terraform projects. While the individual module READMEs are comprehensive, they currently only show local path usage patterns (`source = "./terraform/modules/..."`). Users need clear documentation on how to import these modules from another repository using proper Git source referencing.

The repository is hosted at: `https://github.com/SolomonHD/unifi-cloudflare-glue.git`

## Goal

Add comprehensive documentation showing how to consume the Terraform modules from external projects using Git-based module sourcing with proper version pinning.

## Scope

**In scope:**
- Add "Using as Terraform Modules" section to main README.md with Git-based module source examples
- Update module READMEs (unifi-dns and cloudflare-tunnel) to include Git-based source examples
- Show version pinning best practices using `?ref=v0.1.0` syntax
- Use real GitHub URL: `github.com/SolomonHD/unifi-cloudflare-glue`
- Document both modules with complete usage examples including required variables
- Add examples of consuming modules in external projects

**Out of scope:**
- Terraform Registry publication
- CI/CD pipeline changes
- Module code changes
- Version bumping

## Desired Behavior

### Main README.md Changes

Add a new section after the "Modules" heading that demonstrates:
1. How to source modules from GitHub using the repository URL
2. Version pinning with `?ref=v0.1.0` syntax
3. Complete module usage examples with all required parameters
4. Both modules (unifi-dns and cloudflare-tunnel) with realistic examples

Example structure:
```markdown
## Using as Terraform Modules

### Module Source

You can consume these modules directly from GitHub in your Terraform projects:

```hcl
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"
  # ... configuration
}
```

### Module: unifi-dns

[Complete example with required variables]

### Module: cloudflare-tunnel

[Complete example with required variables]
```

### Individual Module README Changes

Update both module READMEs to include Git-based source examples in the Usage section:

**Before:**
```hcl
module "unifi_dns" {
  source = "./terraform/modules/unifi-dns"
  # ...
}
```

**After:**
```hcl
# Local path (for development within this repo)
module "unifi_dns" {
  source = "./terraform/modules/unifi-dns"
  # ...
}

# Git source (for consuming from external projects)
module "unifi_dns" {
  source = "github.com/SolomonHD/unifi-cloudflare-glue//terraform/modules/unifi-dns?ref=v0.1.0"
  # ...
}
```

## Constraints & Assumptions

- Current version is 0.1.0 (from VERSION file)
- Git tags use `v` prefix (e.g., `v0.1.0`) per Dagger conventions
- Users are familiar with Terraform module sources
- Existing local path examples should remain for developers working within the repo
- SSH module sources (`git@github.com:...`) are not needed; HTTPS is sufficient for public repos

## Acceptance Criteria

- [ ] Main README.md includes new "Using as Terraform Modules" section
- [ ] Section shows Git-based module sourcing with real GitHub URL
- [ ] Both modules (unifi-dns and cloudflare-tunnel) are documented with complete examples
- [ ] Version pinning syntax `?ref=v0.1.0` is demonstrated
- [ ] Individual module READMEs show both local and Git-based source patterns
- [ ] All GitHub references use `github.com/SolomonHD/unifi-cloudflare-glue`
- [ ] No placeholder URLs like `github.com/yourorg/repo` remain
- [ ] Examples include all required variables for each module
- [ ] Documentation maintains consistency with existing style and formatting
