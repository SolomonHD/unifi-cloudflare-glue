# Implementation Tasks: Add KCL Base Schema Definitions

## 1. Schema Implementation

- [x] 1.1 Implement `MACAddress` type with validation
  - Add validation for three formats: `aa:bb:cc:dd:ee:ff`, `aa-bb-cc-dd-ee-ff`, `aabbccddeeff`
  - Add normalization logic to convert all formats to lowercase colon format via `normalize_mac()` function
  - Add check constraints for valid MAC address length (12 or 17 characters)

- [x] 1.2 Implement `Hostname` type with validation
  - Add validation for valid DNS labels per RFC 1123
  - Add length constraints (1-63 characters per label)

- [x] 1.3 Implement `Distribution` enum
  - Define three variants: `unifi_only`, `cloudflare_only`, `both`
  - Set default value to `both`

- [x] 1.4 Implement `Endpoint` schema
  - Add `mac_address` field with `MACAddress` type
  - Add `nic_name` optional field (str)
  - Add `service_cnames` field (list of str for additional CNAMEs)
  - Add doc comments explaining each field

- [x] 1.5 Implement `Service` schema
  - Add `name` field (str) - service identifier
  - Add `port` field (int) with validation (1-65535)
  - Add `protocol` field (str) with enum validation (`http`, `https`, `tcp`)
  - Add `distribution` field with `Distribution` enum
  - Add `internal_hostname` optional field (str)
  - Add `public_hostname` optional field (str)
  - Add doc comments explaining each field

- [x] 1.6 Implement `Entity` schema
  - Add `friendly_hostname` field with `Hostname` type
  - Add `domain` field (str) - base domain for the device
  - Add `endpoints` field (list of Endpoint)
  - Add `services` field (list of Service)
  - Add doc comments explaining each field

## 2. Documentation

- [x] 2.1 Add module-level doc comments to `kcl/schemas/base.k`
  - Explain the purpose of base schemas
  - Document the relationship between Entity, Endpoint, and Service

- [x] 2.2 Add field-level documentation
  - Every schema field has a doc comment
  - Include examples where helpful

## 3. Validation

- [x] 3.1 Run KCL validation
  - Execute `kcl run` to verify schema syntax - PASSED
  - No validation errors

- [x] 3.2 Test schema instantiation
  - Tested Entity, Endpoint, Service instantiation
  - Verified MAC address normalization works correctly (AA-BB-CC-DD-EE-FF -> aa:bb:cc:dd:ee:ff)

## 4. Acceptance Criteria Verification

- [x] 4.1 Verify `kcl/schemas/base.k` contains Entity schema with all required fields
- [x] 4.2 Verify `kcl/schemas/base.k` contains Endpoint schema with MAC validation
- [x] 4.3 Verify `kcl/schemas/base.k` contains Service schema with Distribution enum
- [x] 4.4 Verify MACAddress type accepts all three formats and normalizes to lowercase colons via `normalize_mac()`
- [x] 4.5 Verify Hostname type validates RFC 1123 (1-63 chars)
- [x] 4.6 Verify Distribution enum has exactly three variants: unifi_only, cloudflare_only, both
- [x] 4.7 Verify all schemas have appropriate doc comments explaining usage
- [x] 4.8 Verify KCL module validates without errors (`kcl run` passes)
