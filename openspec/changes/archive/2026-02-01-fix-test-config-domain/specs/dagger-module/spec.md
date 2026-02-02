## MODIFIED Requirements

### Requirement: Test Configuration Domain Parameter

The Dagger module SHALL support configurable UniFi domain in test configuration generation to ensure test DNS records use the correct FQDN matching the Cloudflare zone.

#### Scenario: Default domain behavior
Given: The `_generate_test_configs()` method is called with only the required parameters
When: The `unifi_domain` parameter is not provided (empty string)
Then: The UniFi configuration SHALL use the `cloudflare_zone` value for both device domain and default_domain

#### Scenario: Explicit domain override
Given: The `_generate_test_configs()` method is called with an explicit `unifi_domain` parameter
When: The `unifi_domain` parameter is provided with a non-empty value
Then: The UniFi configuration SHALL use the provided `unifi_domain` value for both device domain and default_domain

#### Scenario: Test integration passes correct domain
Given: The `test_integration()` function is executing
When: It calls `_generate_test_configs()` to create test configurations
Then: It SHALL pass the `cloudflare_zone` value as the `unifi_domain` parameter

#### Scenario: Backward compatibility
Given: Existing code calls `_generate_test_configs()` without the new parameter
When: The method is invoked with the legacy signature
Then: The method SHALL accept the call and default the domain to the cloudflare_zone value
