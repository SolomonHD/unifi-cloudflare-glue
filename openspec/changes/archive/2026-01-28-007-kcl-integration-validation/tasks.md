## 1. Unified Configuration Schema

- [x] 1.1 Create `UnifiedConfig` schema combining UniFiConfig and CloudflareConfig
- [x] 1.2 Add field for UniFi controller configuration
- [x] 1.3 Add field for Cloudflare zone/account configuration
- [x] 1.4 Add field for device-to-tunnel mapping annotations
- [x] 1.5 Test schema instantiation with sample data

## 2. Cross-Provider Validation Functions

- [x] 2.1 Create `get_all_unifi_macs()` lambda to extract all MACs from UniFi devices
- [x] 2.2 Create `get_all_cloudflare_macs()` lambda to extract all MACs from Cloudflare tunnels
- [x] 2.3 Create `validate_mac_consistency()` lambda checking all Cloudflare MACs exist in UniFi
- [x] 2.4 Create `get_all_friendly_hostnames()` lambda to extract device hostnames
- [x] 2.5 Create `validate_hostname_uniqueness()` lambda checking for duplicate hostnames
- [x] 2.6 Create `get_all_public_hostnames()` lambda to extract all public hostnames from tunnels
- [x] 2.7 Create `validate_public_hostname_uniqueness()` lambda checking for duplicates
- [x] 2.8 Create `validate_all()` orchestration function running all validations

## 3. Main Entrypoint and Generation

- [x] 3.1 Create `generate()` function accepting UnifiedConfig
- [x] 3.2 Implement validation-before-generation ordering (fail-fast)
- [x] 3.3 Integrate UniFi generator for unifi_json output
- [x] 3.4 Integrate Cloudflare generator for cloudflare_json output
- [x] 3.5 Return combined result object with both JSON outputs

## 4. Validation Error Messages

- [x] 4.1 Create error formatting for MAC mismatch with available MACs list
- [x] 4.2 Create error formatting for duplicate hostname with conflicting devices
- [x] 4.3 Create error formatting for duplicate public_hostname with conflicting tunnels
- [x] 4.4 Create error formatting for invalid local_service_url domain
- [x] 4.5 Ensure all errors include context and actionable suggestions

## 5. Testing and Documentation

- [x] 5.1 Create test cases for valid unified configuration
- [x] 5.2 Create test cases for MAC mismatch validation failure
- [x] 5.3 Create test cases for duplicate hostname validation failure
- [x] 5.4 Create test cases for duplicate public_hostname validation failure
- [x] 5.5 Verify KCL module runs without errors: `kcl main.k`
- [x] 5.6 Update `kcl/README.md` with unified configuration and validation documentation
