# Change: Add KCL Base Schema Definitions

## Why

KCL (Kusion Configuration Language) serves as the unified configuration layer that bridges UniFi and Cloudflare configurations. The current placeholder schemas in `kcl/schemas/base.k` need to be expanded to define the complete foundational type system that represents the core domain model: Entities (physical devices), Endpoints (network interfaces), and Services (applications running on devices).

Without well-defined base schemas, provider-specific extensions cannot reliably build upon shared concepts, leading to duplicated logic and inconsistent validation across the configuration pipeline.

## What Changes

- **MODIFY** `kcl/schemas/base.k` to implement complete base schemas:
  - `Entity` schema with `friendly_hostname`, `domain`, `endpoints`, and `services` fields
  - `Endpoint` schema with `mac_address`, `nic_name`, and `service_cnames` fields
  - `Service` schema with `name`, `port`, `protocol`, `distribution`, `internal_hostname`, and `public_hostname` fields
  - `MACAddress` type with validation for three formats (colon, hyphen, no-separator)
  - `Hostname` type with DNS label validation
  - `Distribution` enum with `unifi_only`, `cloudflare_only`, and `both` variants

- **ADD** comprehensive doc comments to all schemas explaining their purpose and usage

## Impact

- **Affected specs**: `kcl-module` capability (modified requirements)
- **Affected code**: `kcl/schemas/base.k` (complete implementation)
- **Breaking**: Yes - the current placeholder schemas will be replaced with full implementations

## Dependencies

- Depends on: `project-scaffolding` (directory structure and placeholder files must exist)
