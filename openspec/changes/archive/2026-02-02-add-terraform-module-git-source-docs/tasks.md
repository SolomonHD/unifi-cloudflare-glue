# Tasks: add-terraform-module-git-source-docs

## Documentation Tasks

- [x] Add "Using as Terraform Modules" section to main [`README.md`](../../README.md)
  - [x] Add section after "## Modules" heading
  - [x] Include subsection "### Module Source" explaining Git-based module sourcing
  - [x] Include subsection "### Module: unifi-dns" with complete example
  - [x] Include subsection "### Module: cloudflare-tunnel" with complete example
  - [x] Use real GitHub URL: `github.com/SolomonHD/unifi-cloudflare-glue`
  - [x] Show version pinning syntax: `?ref=v0.1.0`
  - [x] Show double-slash subdirectory syntax: `//terraform/modules/{module-name}`
  - [x] Include all required variables in examples
  - [x] Ensure examples are copy-paste ready

- [x] Update [`terraform/modules/unifi-dns/README.md`](../../terraform/modules/unifi-dns/README.md)
  - [x] Locate "Usage" or "## Usage" section
  - [x] Add comment "# Local path (for development within this repo)" above existing local example
  - [x] Add new subsection with comment "# Git source (for consuming from external projects)"
  - [x] Include Git-based module source example with `?ref=v0.1.0`
  - [x] Preserve existing example structure and variables
  - [x] Ensure formatting consistency with existing content

- [x] Update [`terraform/modules/cloudflare-tunnel/README.md`](../../terraform/modules/cloudflare-tunnel/README.md)
  - [x] Locate "Usage" or "## Usage" section
  - [x] Add comment "# Local path (for development within this repo)" above existing local example
  - [x] Add new subsection with comment "# Git source (for consuming from external projects)"
  - [x] Include Git-based module source example with `?ref=v0.1.0`
  - [x] Preserve existing example structure and variables
  - [x] Ensure formatting consistency with existing content

## Verification Tasks

- [x] Verify no placeholder URLs remain (`yourorg`, `yourusername`, etc.)
- [x] Verify all version references use `v0.1.0` (matching VERSION file)
- [x] Verify all GitHub URLs use `github.com/SolomonHD/unifi-cloudflare-glue`
- [x] Verify code blocks use proper syntax highlighting (```hcl)
- [x] Verify examples include all required variables
- [x] Verify formatting matches existing documentation style
- [x] Check that heading hierarchy is correct
- [x] Spell-check technical terms are used consistently

## Dependencies

- Current VERSION file content (0.1.0) - used for version pinning examples
- Existing module README structure - enhanced, not replaced
- Main README "Modules" section location - new section added after it
