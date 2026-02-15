# Validation Testing Example
#
# This example demonstrates the validation error handling workflow.
# It shows how validation errors are caught and how to fix them.
#
# Usage:
#   kcl run main.k                    # Run all tests
#
# Prerequisites:
#   kcl mod add unifi_cloudflare_glue --git https://github.com/SolomonHD/unifi-cloudflare-glue --tag v0.4.0
import unifi_cloudflare_glue.schemas.unifi as unifi
import unifi_cloudflare_glue.schemas.cloudflare as cloudflare
import unifi_cloudflare_glue.main as main

# ============================================================================
# SCENARIO 1: Configuration with MAC Mismatch Error
# ============================================================================
#
# This configuration has a MAC_CONSISTENCY_ERROR because the Cloudflare tunnel
# references a MAC address (aa:bb:cc:dd:ee:99) that doesn't exist in the
# UniFi device list.
problematic_unifi = unifi.UniFiConfig {
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
    }
    devices = [
        unifi.UniFiEntity {
            friendly_hostname = "server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    # This MAC is in UniFi
                    mac_address = "aa:bb:cc:dd:ee:01"
                    nic_name = "eth0"
                }
            ]
            services = []
        }
    ]
}

problematic_cloudflare = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "test-account-id"
    default_no_tls_verify = False
    tunnels = {
        # This MAC does NOT exist in UniFi - will cause validation error!
        "aa:bb:cc:dd:ee:99": cloudflare.CloudflareTunnel {
            tunnel_name = "server-tunnel"
            mac_address = "aa:bb:cc:dd:ee:99"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "app.example.com"
                    local_service_url = "http://app.internal.lan:8080"
                }
            ]
        }
    }
}

problematic_config = main.UnifiedConfig {
    unifi = problematic_unifi
    cloudflare = problematic_cloudflare
}

# ============================================================================
# SCENARIO 2: Fixed Configuration (MAC addresses match)
# ============================================================================
#
# This configuration is valid because the Cloudflare tunnel MAC matches
# a MAC address in the UniFi device list.
fixed_unifi = unifi.UniFiConfig {
    default_domain = "internal.lan"
    unifi_controller = unifi.UniFiController {
        host = "unifi.internal.lan"
    }
    devices = [
        unifi.UniFiEntity {
            friendly_hostname = "server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa:bb:cc:dd:ee:01"
                    nic_name = "eth0"
                }
            ]
            services = []
        }
    ]
}

fixed_cloudflare = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "test-account-id"
    default_no_tls_verify = False
    tunnels = {
        # This MAC matches the UniFi device - valid!
        "aa:bb:cc:dd:ee:01": cloudflare.CloudflareTunnel {
            tunnel_name = "server-tunnel"
            mac_address = "aa:bb:cc:dd:ee:01"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "app.example.com"
                    local_service_url = "http://app.internal.lan:8080"
                }
            ]
        }
    }
}

fixed_config = main.UnifiedConfig {
    unifi = fixed_unifi
    cloudflare = fixed_cloudflare
}

# ============================================================================
# VALIDATION TESTS
# ============================================================================

# Test 1: Run validation on problematic config
problematic_validation = main.validate_only(problematic_config)

# Test 2: Run validation on fixed config
fixed_validation = main.validate_only(fixed_config)

# Test 3: Attempt generation with problematic config (will show errors)
problematic_result = main.generate_with_output(problematic_config)

# Test 4: Generation with fixed config (will succeed)
fixed_result = main.generate_with_output(fixed_config)

# ============================================================================
# OUTPUT SUMMARY
# ============================================================================
{
    # Validation-only mode results
    validation_summary = {
        problematic_config = {
            valid = problematic_validation["valid"]
            error_count = problematic_validation["error_count"]
            errors = problematic_validation["errors"]
        }
        fixed_config = {
            valid = fixed_validation["valid"]
            error_count = fixed_validation["error_count"]
            errors = fixed_validation["errors"]
        }
    }
    # Full generation results
    generation_results = {
        problematic_config = {
            valid = problematic_result.valid
            has_unifi_json = len(problematic_result.unifi_json) > 0
            has_cloudflare_json = len(problematic_result.cloudflare_json) > 0
        }
        fixed_config = {
            valid = fixed_result.valid
            has_unifi_json = len(fixed_result.unifi_json) > 0
            has_cloudflare_json = len(fixed_result.cloudflare_json) > 0
        }
    }
}
