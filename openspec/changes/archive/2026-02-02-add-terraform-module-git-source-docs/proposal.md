# Proposal: Add Terraform Module Git Source Documentation

## Summary

Add comprehensive documentation showing how to consume the `unifi-dns` and `cloudflare-tunnel` Terraform modules from external projects using Git-based module sourcing with proper version pinning.

## Context

The `unifi-cloudflare-glue` repository contains two reusable Terraform modules that are designed to be consumed by external projects. Currently:

- Individual module READMEs only show local path usage (`source = "./terraform/modules/..."`)
- No examples demonstrate Git-based module sourcing for external consumption
- Main README doesn't explain how to use these modules in other projects
- Users must infer the correct Git source syntax and version pinning patterns

This gap creates friction for users who want to consume these modules as infrastructure dependencies in their own Terraform projects.

## Goals

1. **Main README Enhancement**: Add a new "Using as Terraform Modules" section showing how to consume modules from GitHub
2. **Module README Updates**: Update individual module READMEs to show both local and Git-based source patterns
3. **Version Pinning**: Demonstrate the `?ref=v0.1.0` syntax for pinning to specific versions
4. **Complete Examples**: Provide full working examples with all required variables
5. **Consistency**: Use the real GitHub URL (`github.com/SolomonHD/unifi-cloudflare-glue`) throughout

## Non-Goals

- Terraform Registry publication (future work)
- CI/CD pipeline changes
- Module code modifications
- Version bumping or releases

## Impact

### Users

**Benefit**: Clear guidance on consuming modules in their own Terraform projects with proper version pinning

**Migration**: None required; this is purely additive documentation

### Maintainers

**Benefit**: Reduced support burden from common "how do I use this?" questions

**Considerations**: Documentation must be kept in sync with module interfaces

## Open Questions

None - the prompt is well-specified with clear examples and acceptance criteria.

## Dependencies

- Existing module READMEs (will be enhanced)
- Main README structure (will add new section)
- Current version (0.1.0) for examples

## Timeline

Single documentation-only change, implementable immediately after proposal approval.
