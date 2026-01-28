# Tasks: KCL Cloudflare Generator
 
 ## Implementation Tasks
 
 - [x] Import schemas in generator file
   - Add imports for `kcl/schemas/base.k` and `kcl/schemas/cloudflare.k`
   - Verify schema types are accessible
 
 - [x] Implement `normalize_mac()` wrapper
   - Reuse existing function from base.k
   - Ensure it's accessible within generator scope
 
 - [x] Implement service filtering function
   - Create lambda to filter services by distribution
   - Include `cloudflare_only` and `both` distributions
   - Exclude `unifi_only` services
 
 - [x] Implement `local_service_url` construction
   - Create lambda to build URL from service protocol, hostname, and port
   - Use `service.internal_hostname` if available
   - Fall back to `device.friendly_hostname` + internal domain if needed
   - Format: `{protocol}://{hostname}:{port}`
 
 - [x] Implement `public_hostname` resolution
   - Use `service.public_hostname` if explicitly set
   - Generate from `service.name` + zone_name if not set
   - Ensure all public hostnames are subdomains of configured zone
 
 - [x] Implement tunnel transformation function
   - Create lambda to transform `CloudflareTunnel` to tunnel record
   - Key tunnels by normalized MAC address
   - Transform all services for the tunnel
 
 - [x] Implement `generate_cloudflare_config()` function
   - Accept `CloudflareConfig` parameter
   - Transform all tunnels
   - Return dictionary with `zone_name`, `account_id`, and `tunnels`
 
 - [x] Implement DNS loop prevention validation
   - Validate `local_service_url` uses internal domain only
   - Check that URL does not contain public zone name
   - Log warnings for potential issues
 
 - [x] Add sample configuration for testing
   - Create test `CloudflareConfig` instance
   - Include multiple tunnels with various configurations
   - Include services with different distributions
   - Test DNS loop prevention scenarios
 
 - [x] Validate generator output
   - Run `kcl run generators/cloudflare.k`
   - Verify JSON is valid
   - Check output matches expected schema
 
 - [x] Test MAC normalization
   - Test various MAC formats (colon, hyphen, no-separator)
   - Verify lowercase output
   - Ensure MAC is used as dictionary key
 
 - [x] Test service filtering
   - Verify `unifi_only` services are excluded
   - Verify `cloudflare_only` and `both` services are included
 
 - [x] Test URL construction
   - Verify `local_service_url` format
   - Test hostname priority (internal_hostname vs fallback)
   - Verify DNS loop prevention catches violations
 
 - [x] Update README documentation
   - Document generator usage
   - Add example invocation
   - Document DNS loop prevention constraints
 
 ## Definition of Done
 
 - [x] `kcl/generators/cloudflare.k` contains complete implementation
 - [x] Generator outputs valid JSON matching Cloudflare module schema
 - [x] All MAC addresses normalized to lowercase colon format
 - [x] Tunnels correctly keyed by MAC address
 - [x] Services correctly filtered by distribution
 - [x] `local_service_url` constructed with internal domains only
 - [x] DNS loop prevention validation implemented
 - [x] Generator can be called with `generate_cloudflare_config(config)`
 - [x] Sample configuration demonstrates all features

## Dependencies

- Requires: `004-kcl-cloudflare-schemas` (completed - archived)
- Blocks: `007-kcl-integration-validation`
