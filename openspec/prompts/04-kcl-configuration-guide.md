# OpenSpec Prompt: KCL Configuration Guide

## Context

The current documentation provides minimal guidance on KCL schemas and configuration. Users need comprehensive documentation to understand how to define services, validate configurations, and debug KCL errors.

## Goal

Create comprehensive KCL documentation that explains the schema structure, validation rules, common configuration patterns, and debugging techniques.

## Scope

### In Scope

1. Create [`docs/kcl-guide.md`](../../docs/kcl-guide.md) with complete KCL reference
2. Document all schemas:
   - Base schemas (Entity, Endpoint, Service, MACAddress)
   - UniFi-specific schemas
   - Cloudflare-specific schemas
3. Explain validation rules and why they exist
4. Add common configuration patterns
5. Add debugging guide for KCL errors
6. Create additional examples in [`examples/`](../../examples/) directory
7. Link from main docs to KCL module README

### Out of Scope

- Changes to KCL schemas themselves
- New KCL features or validators
- KCL language tutorial (link to official docs)
- Generator implementation details

## Desired Behavior

### Documentation Structure: docs/kcl-guide.md

```markdown
# KCL Configuration Guide

## Overview

KCL (KCL Configuration Language) provides type-safe configuration with validation.

## Schema Reference

### Base Schemas

#### Entity
Base type for physical or logical entities (devices, services)

#### Endpoint  
Network endpoint with URL and optional port

#### Service
Service configuration linking entities and endpoints

#### MACAddress
MAC address type with validation

### UniFi Schemas

Device, NIC, DNS record configuration

### Cloudflare Schemas

Tunnel, tunnel service, DNS configuration

## Configuration Patterns

### Pattern 1: Single Service per Device
### Pattern 2: Multiple Services per Device  
### Pattern 3: Internal-Only Services
### Pattern 4: External-Only Services

## Validation Rules

### MAC Address Format
### Hostname Requirements
### DNS Loop Prevention
### One Tunnel Per Device

## Debugging KCL Errors

### Syntax Errors
### Type Errors
### Validation Errors
### Common Mistakes

## Testing Your Configuration

```bash
kcl run main.k  # Validate syntax and types
kcl run generators/unifi.k > /dev/null  # Test UniFi generation
kcl run generators/cloudflare.k > /dev/null  # Test Cloudflare generation
```

## Examples

Link to examples directory
```

### Example Configurations to Add

Add to `examples/` directory:

#### examples/single-service/

Simple example with one device, one service

#### examples/multiple-services/

Device with multiple services (web, API, admin)

#### examples/internal-only/

Services only accessible internally (no Cloudflare tunnel)

#### examples/external-only/

Services only accessible via Cloudflare (no internal DNS)

## Constraints & Assumptions

### Constraints

- Must match actual KCL schema implementation
- Examples must be tested and working
- Link to official KCL docs for language features
- Focus on this project's schemas, not general KCL

### Assumptions

- Users have basic understanding of configuration languages
- Users can read KCL schema files
- Users want practical examples more than theory
- Users will encounter validation errors and need debugging help

## Acceptance Criteria

- [ ] [`docs/kcl-guide.md`](../../docs/kcl-guide.md) created with comprehensive guide
- [ ] All base schemas documented with examples
- [ ] UniFi schemas documented
- [ ] Cloudflare schemas documented
- [ ] Validation rules explained with rationale
- [ ] Common configuration patterns provided
- [ ] Debugging guide for KCL errors
- [ ] Testing section with validation commands
- [ ] At least 4 example configurations added to [`examples/`](../../examples/)
- [ ] Link added from main README to KCL guide
- [ ] Link added from [`kcl/README.md`](../../kcl/README.md) to docs
- [ ] Cross-references to example directory

## Expected Files/Areas Touched

- `docs/kcl-guide.md` (new)
- `examples/single-service/` (new directory)
  - `main.k` (new)
  - `README.md` (new)
- `examples/multiple-services/` (new directory)
  - `main.k` (new)
  - `README.md` (new)
- `examples/internal-only/` (new directory)
  - `main.k` (new)
  - `README.md` (new)
- `examples/external-only/` (new directory)
  - `main.k` (new)
  - `README.md` (new)
- `kcl/README.md` (add link to docs)
- `docs/README.md` (update index)
- `README.md` (add link)

## Dependencies

- Prompt 01 (docs structure must exist)

## Notes

- KCL is central to this project but barely documented
- Users struggle with validation errors without explanation
- Common patterns will reduce support burden
- Link to official KCL docs for language features, focus on project-specific schemas
