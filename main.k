# KCL Main Entrypoint - Unified Configuration and Cross-Provider Validation
#
# This module provides the UnifiedConfig schema that combines UniFi and Cloudflare
# configurations into a single source of truth. It implements comprehensive
# cross-provider validation to catch configuration errors before generation.
#
# Usage:
#     import .main
#
#     config = main.UnifiedConfig {
#         unifi = {...}
#         cloudflare = {...}
#     }
#     result = main.generate(config)

# Import schemas
import .schemas.base
import .schemas.unifi
import .schemas.cloudflare

# Import generators
import .generators.unifi as unifi_gen
import .generators.cloudflare as cloudflare_gen

# =============================================================================
# Section 1: Unified Configuration Schema
# =============================================================================

# DeviceToTunnelMapping provides annotation for linking devices to tunnels
schema DeviceToTunnelMapping:
    """Maps a UniFi device to a Cloudflare tunnel by MAC address.

    This annotation creates explicit linkage between the UniFi device
    representation and its Cloudflare tunnel configuration.

    Attributes:
        device_hostname: The friendly_hostname of the UniFi device
        tunnel_name: The name of the Cloudflare tunnel
        mac_address: The MAC address (normalized) linking both
    """
    device_hostname: str
    tunnel_name: str
    mac_address: str

# UnifiedConfig is the root configuration combining UniFi and Cloudflare settings
schema UnifiedConfig:
    """Root configuration container combining UniFi and Cloudflare settings.

    This schema serves as the single source of truth for the entire
    infrastructure configuration, enabling cross-provider validation.

    Attributes:
        unifi: UniFi configuration with devices and controller settings
        cloudflare: Cloudflare configuration with tunnels and zone settings
        mappings: Optional explicit device-to-tunnel mappings

    Validation:
        - UniFi devices and Cloudflare tunnels are validated together
        - All Cloudflare MACs must exist in UniFi devices
        - Hostnames must be unique across devices
        - Public hostnames must be unique across tunnel services
    """
    unifi: unifi.UniFiConfig
    cloudflare: cloudflare.CloudflareConfig
    mappings: [DeviceToTunnelMapping] = []

    check:
        # Schema-level validations can be added here
        # Cross-field validations are done via validation functions
        True, "Configuration valid"

# =============================================================================
# Section 2: Cross-Provider Validation Functions
# =============================================================================

# Extract all MAC addresses from UniFi devices
get_all_unifi_macs = lambda cfg: UnifiedConfig -> [str] {
    [base.normalize_mac(ep.mac_address) for device in cfg.unifi.devices for ep in device.endpoints]
}

# Extract all MAC addresses from Cloudflare tunnels
get_all_cloudflare_macs = lambda cfg: UnifiedConfig -> [str] {
    [base.normalize_mac(tunnel.mac_address) for _, tunnel in cfg.cloudflare.tunnels]
}

# Find MAC addresses in Cloudflare that don't exist in UniFi
find_missing_macs = lambda cfg: UnifiedConfig -> [str] {
    unifi_macs = get_all_unifi_macs(cfg)
    cloudflare_macs = get_all_cloudflare_macs(cfg)

    [mac for mac in cloudflare_macs if mac not in unifi_macs]
}

# Validate that all Cloudflare MACs exist in UniFi devices
# Returns error dict if invalid, empty dict if valid
validate_mac_consistency = lambda cfg: UnifiedConfig -> {str:str} {
    missing_macs = find_missing_macs(cfg)
    unifi_macs = get_all_unifi_macs(cfg)

    # Use conditional expression - must return a dict
    {
        "error" = "MAC_CONSISTENCY_ERROR"
        "message" = "Cloudflare tunnels reference MAC addresses not found in UniFi devices"
        "missing_macs" = str(missing_macs)
        "available_unifi_macs" = str(unifi_macs)
        "suggestion" = "Add UniFi devices with these MAC addresses or update tunnel configurations"
    } if len(missing_macs) > 0 else {}
}

# Extract all friendly hostnames from UniFi devices
get_all_friendly_hostnames = lambda cfg: UnifiedConfig -> [str] {
    [device.friendly_hostname for device in cfg.unifi.devices]
}

# Count occurrences of hostnames and return duplicates
find_duplicate_hostnames = lambda cfg: UnifiedConfig -> {str:int} {
    hostnames = get_all_friendly_hostnames(cfg)

    {hostname: sum([1 for h in hostnames if h == hostname]) for hostname in hostnames if sum([1 for h in hostnames if h == hostname]) > 1}
}

# Validate that all device hostnames are unique
validate_hostname_uniqueness = lambda cfg: UnifiedConfig -> {str:str} {
    duplicates = find_duplicate_hostnames(cfg)

    # Build conflicts list using comprehension
    conflicts = ["${hostname}: [" + ", ".join([device.friendly_hostname for device in cfg.unifi.devices if device.friendly_hostname == hostname]) + "]" for hostname, _ in duplicates]

    # Use conditional expression
    {
        "error" = "DUPLICATE_HOSTNAME_ERROR"
        "message" = "Duplicate friendly_hostnames found across devices"
        "duplicate_hostnames" = str([k for k, _ in duplicates])
        "conflicts" = str(conflicts)
        "suggestion" = "Use unique friendly_hostnames for each device"
    } if len(duplicates) > 0 else {}
}

# Extract all public hostnames from Cloudflare tunnel services
get_all_public_hostnames = lambda cfg: UnifiedConfig -> [str] {
    [svc.public_hostname for _, tunnel in cfg.cloudflare.tunnels for svc in tunnel.services]
}

# Find duplicate public hostnames
find_duplicate_public_hostnames = lambda cfg: UnifiedConfig -> {str:int} {
    public_hostnames = get_all_public_hostnames(cfg)

    {hostname: sum([1 for h in public_hostnames if h == hostname]) for hostname in public_hostnames if sum([1 for h in public_hostnames if h == hostname]) > 1}
}

# Validate that all public hostnames are unique across tunnels
validate_public_hostname_uniqueness = lambda cfg: UnifiedConfig -> {str:str} {
    duplicates = find_duplicate_public_hostnames(cfg)

    # Build conflicts list
    conflicts = ["${hostname}: [" + ", ".join([tunnel.tunnel_name for _, tunnel in cfg.cloudflare.tunnels for svc in tunnel.services if svc.public_hostname == hostname]) + "]" for hostname, _ in duplicates]

    # Use conditional expression
    {
        "error" = "DUPLICATE_PUBLIC_HOSTNAME_ERROR"
        "message" = "Duplicate public_hostnames found across tunnel services"
        "duplicate_public_hostnames" = str([k for k, _ in duplicates])
        "conflicts" = str(conflicts)
        "suggestion" = "Use unique public_hostnames for each tunnel service"
    } if len(duplicates) > 0 else {}
}

# Find services with invalid domain syntax
find_invalid_domain_services = lambda cfg: UnifiedConfig -> [str] {
    ["${tunnel.tunnel_name}: ${svc.public_hostname} -> ${svc.local_service_url}" for _, tunnel in cfg.cloudflare.tunnels for svc in tunnel.services if not cloudflare.is_valid_domain(svc.local_service_url)]
}

# Validate that all local_service_url values use valid domain syntax
validate_domain_syntax = lambda cfg: UnifiedConfig -> {str:str} {
    invalid_services = find_invalid_domain_services(cfg)

    # Use conditional expression
    {
        "error" = "DOMAIN_SYNTAX_ERROR"
        "message" = "local_service_url values must use valid domain syntax (RFC 1123)"
        "violations" = str(invalid_services)
        "valid_domains" = "Any valid domain: internal (.internal.lan, .local, .home) or public (e.g., .com, .net, .io)"
        "suggestion" = "Ensure local_service_url uses a valid domain format (e.g., http://service.internal.lan:8080 or http://service.mycompany.com:8080)"
    } if len(invalid_services) > 0 else {}
}

# Run all validations and collect errors
validate_all = lambda cfg: UnifiedConfig -> [{str:str}] {
    [result for result in [
        validate_mac_consistency(cfg)
        validate_hostname_uniqueness(cfg)
        validate_public_hostname_uniqueness(cfg)
        validate_domain_syntax(cfg)
    ] if len(result) > 0]
}

# =============================================================================
# Section 3: Error Formatting and Reporting
# =============================================================================

# Format MAC_CONSISTENCY_ERROR
format_mac_error = lambda error: {str:str} -> str {
    "✗ ${error['error']}\n  Message: ${error['message']}\n  Missing MACs: ${error['missing_macs']}\n  Available UniFi MACs: ${error['available_unifi_macs']}\n  Suggestion: ${error['suggestion']}\n"
}

# Format DUPLICATE_HOSTNAME_ERROR
format_hostname_error = lambda error: {str:str} -> str {
    "✗ ${error['error']}\n  Message: ${error['message']}\n  Duplicate Hostnames: ${error['duplicate_hostnames']}\n  Conflicts: ${error['conflicts']}\n  Suggestion: ${error['suggestion']}\n"
}

# Format DUPLICATE_PUBLIC_HOSTNAME_ERROR
format_public_hostname_error = lambda error: {str:str} -> str {
    "✗ ${error['error']}\n  Message: ${error['message']}\n  Duplicate Public Hostnames: ${error['duplicate_public_hostnames']}\n  Conflicts: ${error['conflicts']}\n  Suggestion: ${error['suggestion']}\n"
}

# Format DOMAIN_SYNTAX_ERROR
format_domain_error = lambda error: {str:str} -> str {
    "✗ ${error['error']}\n  Message: ${error['message']}\n  Violations: ${error['violations']}\n  Valid Examples: ${error['valid_domains']}\n  Suggestion: ${error['suggestion']}\n"
}

# Format a single validation error using dict field access
format_single_error = lambda error: {str:str} -> str {
    format_mac_error(error) if 'missing_macs' in error else (format_hostname_error(error) if 'duplicate_hostnames' in error else (format_public_hostname_error(error) if 'duplicate_public_hostnames' in error else (format_domain_error(error) if 'violations' in error else "✗ UNKNOWN_ERROR\n")))
}

# Format validation errors for human-readable output
format_validation_errors = lambda errors: [{str:str}] -> str {
    header = "✗ VALIDATION FAILED\n\n"
    error_count = "Found ${str(len(errors))} validation error(s):\n\n"

    # Format each error and join with blank line separator
    formatted_errors = [format_single_error(err) for err in errors]

    header + error_count + "\n".join(formatted_errors)
}

# =============================================================================
# Section 4: Main Entrypoint and Generation
# =============================================================================

# GenerateResult is the output of the generate() function
schema GenerateResult:
    """Result of generate() containing both UniFi and Cloudflare JSON outputs.

    Attributes:
        unifi_json: UniFi-compatible JSON configuration
        cloudflare_json: Cloudflare-compatible JSON configuration
        valid: Whether the configuration passed all validations
        errors: List of validation errors if any
    """
    unifi_json: any
    cloudflare_json: any
    valid: bool
    errors: [{str:str}] = []

# Build result for valid configuration
build_success_result = lambda cfg: UnifiedConfig -> GenerateResult {
    GenerateResult {
        unifi_json = unifi_gen.generate_unifi_config(cfg.unifi)
        cloudflare_json = cloudflare_gen.generate_cloudflare_config(cfg.cloudflare)
        valid = True
        errors = []
    }
}

# Build result for invalid configuration
build_error_result = lambda errors: [{str:str}] -> GenerateResult {
    GenerateResult {
        unifi_json = {}
        cloudflare_json = {}
        valid = False
        errors = errors
    }
}

# generate validates configuration and produces JSON outputs
# This is the main entrypoint for the KCL module
generate = lambda cfg: UnifiedConfig -> GenerateResult {
    errors = validate_all(cfg)

    # Use conditional expression for the entire result
    build_error_result(errors) if len(errors) > 0 else build_success_result(cfg)
}

# generate_with_output validates configuration and produces JSON outputs
# This variant prints validation results and only outputs JSON when valid
generate_with_output = lambda cfg: UnifiedConfig -> any {
    errors = validate_all(cfg)
    result = generate(cfg)

    # When validation fails: print errors, return error result
    # When validation passes: print success, return result
    # Use print() + result pattern: print returns None, so we evaluate both and return result
    print(format_validation_errors(errors)) or result if len(errors) > 0 else print("✓ VALIDATION PASSED\n") or result
}

# validate_only runs validation without generation
# Returns validation summary for pre-deployment checks
validate_only = lambda cfg: UnifiedConfig -> {str:any} {
    errors = validate_all(cfg)

    {
        "valid" = len(errors) == 0
        "error_count" = len(errors)
        "errors" = errors
    }
}

# =============================================================================
# Section 5: Sample Configuration for Testing
# =============================================================================

# Sample UniFi configuration
sample_unifi_config = unifi.UniFiConfig {
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
    }
    devices = [
        unifi.UniFiEntity {
            friendly_hostname = "media-server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa:bb:cc:dd:ee:01"
                    nic_name = "eth0"
                }
            ]
            services = [
                unifi.Service {
                    name = "jellyfin"
                    port = 8096
                    protocol = "http"
                    distribution = "both"
                    internal_hostname = "jellyfin.internal.lan"
                    public_hostname = "jellyfin.example.com"
                }
                unifi.Service {
                    name = "plex"
                    port = 32400
                    protocol = "https"
                    distribution = "unifi_only"
                    internal_hostname = "plex.internal.lan"
                }
            ]
        }
        unifi.UniFiEntity {
            friendly_hostname = "nas-server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa:bb:cc:dd:ee:02"
                    nic_name = "eth0"
                }
            ]
            services = [
                unifi.Service {
                    name = "files"
                    port = 443
                    protocol = "https"
                    distribution = "cloudflare_only"
                    public_hostname = "files.example.com"
                    internal_hostname = "nas.internal.lan"
                }
            ]
        }
    ]
}

# Sample Cloudflare configuration (matching UniFi MACs)
sample_cloudflare_config = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    default_no_tls_verify = False
    tunnels = {
        "aa:bb:cc:dd:ee:01": cloudflare.CloudflareTunnel {
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:01"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "jellyfin.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
            ]
        }
        "aa:bb:cc:dd:ee:02": cloudflare.CloudflareTunnel {
            tunnel_name = "nas-server"
            mac_address = "aa:bb:cc:dd:ee:02"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "files.example.com"
                    local_service_url = "https://nas.internal.lan:443"
                    no_tls_verify = True
                }
            ]
        }
    }
}

# Sample unified configuration
sample_unified_config = UnifiedConfig {
    unifi = sample_unifi_config
    cloudflare = sample_cloudflare_config
    mappings = [
        DeviceToTunnelMapping {
            device_hostname = "media-server"
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:01"
        }
        DeviceToTunnelMapping {
            device_hostname = "nas-server"
            tunnel_name = "nas-server"
            mac_address = "aa:bb:cc:dd:ee:02"
        }
    ]
}

# Generate and output the result
result = generate(sample_unified_config)
