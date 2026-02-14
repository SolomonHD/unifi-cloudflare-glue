# KCL Validation Test Cases
#
# This file tests the cross-provider validation logic in main.k
# Run with: kcl test_validation.k
import .schemas.unifi
import .schemas.cloudflare
import .main

# =============================================================================
# Test 1: Valid Configuration
# =============================================================================
valid_unifi = unifi.UniFiConfig {
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
                }
            ]
            services = []
        }
        unifi.UniFiEntity {
            friendly_hostname = "nas-server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa:bb:cc:dd:ee:02"
                }
            ]
            services = []
        }
    ]
}

valid_cloudflare = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
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
                }
            ]
        }
    }
}

valid_config = main.UnifiedConfig {
    unifi = valid_unifi
    cloudflare = valid_cloudflare
}

valid_result = main.generate(valid_config)

# =============================================================================
# Test 2: MAC Mismatch - Cloudflare references MAC not in UniFi
# =============================================================================
mac_mismatch_cloudflare = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    tunnels = {
        "aa:bb:cc:dd:ee:99": cloudflare.CloudflareTunnel {
            tunnel_name = "unknown-server"
            mac_address = "aa:bb:cc:dd:ee:99"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "unknown.example.com"
                    local_service_url = "http://unknown.internal.lan:8080"
                }
            ]
        }
    }
}

mac_mismatch_config = main.UnifiedConfig {
    unifi = valid_unifi
    cloudflare = mac_mismatch_cloudflare
}

mac_mismatch_result = main.generate(mac_mismatch_config)

# =============================================================================
# Test 3: Duplicate Hostnames - Two devices with same hostname
# =============================================================================
duplicate_hostname_unifi = unifi.UniFiConfig {
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
                }
            ]
            services = []
        }
        unifi.UniFiEntity {
            friendly_hostname = "media-server"
            domain = "internal.lan"
            endpoints = [
                unifi.UniFiEndpoint {
                    mac_address = "aa:bb:cc:dd:ee:02"
                }
            ]
            services = []
        }
    ]
}

duplicate_hostname_config = main.UnifiedConfig {
    unifi = duplicate_hostname_unifi
    cloudflare = valid_cloudflare
}

duplicate_hostname_result = main.generate(duplicate_hostname_config)

# =============================================================================
# Test 4: Duplicate Public Hostnames - Two services with same public hostname
# =============================================================================
duplicate_public_hostname_cloudflare = cloudflare.CloudflareConfig {
    zone_name = "example.com"
    account_id = "1234567890abcdef1234567890abcdef"
    tunnels = {
        "aa:bb:cc:dd:ee:01": cloudflare.CloudflareTunnel {
            tunnel_name = "media-server"
            mac_address = "aa:bb:cc:dd:ee:01"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "same.example.com"
                    local_service_url = "http://jellyfin.internal.lan:8096"
                }
            ]
        }
        "aa:bb:cc:dd:ee:02": cloudflare.CloudflareTunnel {
            tunnel_name = "nas-server"
            mac_address = "aa:bb:cc:dd:ee:02"
            services = [
                cloudflare.TunnelService {
                    public_hostname = "same.example.com"
                    local_service_url = "https://nas.internal.lan:443"
                }
            ]
        }
    }
}

duplicate_public_hostname_config = main.UnifiedConfig {
    unifi = valid_unifi
    cloudflare = duplicate_public_hostname_cloudflare
}

duplicate_public_hostname_result = main.generate(duplicate_public_hostname_config)

# =============================================================================
# Test 5: Domain Syntax Validation - Direct function tests
# =============================================================================
# Test the is_valid_domain function directly for various domain formats

# Valid domains
test_valid_internal = cloudflare.is_valid_domain("http://jellyfin.internal.lan:8096")
test_valid_public = cloudflare.is_valid_domain("http://jellyfin.mycompany.com:8096")
test_valid_simple = cloudflare.is_valid_domain("http://server.local")
test_valid_two_level = cloudflare.is_valid_domain("http://example.co.uk:8080")

# Invalid domains
test_invalid_consecutive_dots = cloudflare.is_valid_domain("http://jellyfin..internal.lan")
test_invalid_hyphen_start = cloudflare.is_valid_domain("http://-server.internal.lan")
test_invalid_hyphen_end = cloudflare.is_valid_domain("http://server-.internal.lan")
test_invalid_tld = cloudflare.is_valid_domain("http://jellyfin.example.a")
test_invalid_leading_dot = cloudflare.is_valid_domain("http://.example.com")
test_invalid_trailing_dot = cloudflare.is_valid_domain("http://example.com.")
test_invalid_no_tld = cloudflare.is_valid_domain("http://localhost")
test_invalid_empty_label = cloudflare.is_valid_domain("http://a..b.com")

# =============================================================================
# Test Results Output
# =============================================================================
test_results = {
    valid_config_test = {
        name = "Valid Configuration"
        passed = valid_result.valid
        errors = valid_result.errors
    }
    mac_mismatch_test = {
        name = "MAC Mismatch Detection"
        passed = not mac_mismatch_result.valid
        expected_error = "MAC_CONSISTENCY_ERROR"
        actual_error = mac_mismatch_result.errors[0]["error"] if len(mac_mismatch_result.errors) > 0 else "NONE"
    }
    duplicate_hostname_test = {
        name = "Duplicate Hostname Detection"
        passed = not duplicate_hostname_result.valid
        expected_error = "DUPLICATE_HOSTNAME_ERROR"
        actual_error = duplicate_hostname_result.errors[0]["error"] if len(duplicate_hostname_result.errors) > 0 else "NONE"
    }
    duplicate_public_hostname_test = {
        name = "Duplicate Public Hostname Detection"
        passed = not duplicate_public_hostname_result.valid
        expected_error = "DUPLICATE_PUBLIC_HOSTNAME_ERROR"
        actual_error = duplicate_public_hostname_result.errors[0]["error"] if len(duplicate_public_hostname_result.errors) > 0 else "NONE"
    }
    valid_internal_domain_test = {
        name = "Valid Internal Domain"
        passed = test_valid_internal
    }
    valid_public_domain_test = {
        name = "Valid Public Domain"
        passed = test_valid_public
    }
    valid_simple_test = {
        name = "Valid Simple Domain"
        passed = test_valid_simple
    }
    valid_two_level_test = {
        name = "Valid Two-Level TLD"
        passed = test_valid_two_level
    }
    invalid_consecutive_dots_test = {
        name = "Invalid: Consecutive Dots"
        passed = not test_invalid_consecutive_dots
    }
    invalid_hyphen_start_test = {
        name = "Invalid: Hyphen at Start"
        passed = not test_invalid_hyphen_start
    }
    invalid_hyphen_end_test = {
        name = "Invalid: Hyphen at End"
        passed = not test_invalid_hyphen_end
    }
    invalid_tld_test = {
        name = "Invalid: Single-char TLD"
        passed = not test_invalid_tld
    }
    invalid_leading_dot_test = {
        name = "Invalid: Leading Dot"
        passed = not test_invalid_leading_dot
    }
    invalid_trailing_dot_test = {
        name = "Invalid: Trailing Dot"
        passed = not test_invalid_trailing_dot
    }
    invalid_no_tld_test = {
        name = "Invalid: No TLD"
        passed = not test_invalid_no_tld
    }
    invalid_empty_label_test = {
        name = "Invalid: Empty Label"
        passed = not test_invalid_empty_label
    }
}

# Summary
all_passed = test_results.valid_config_test.passed and test_results.mac_mismatch_test.passed and test_results.duplicate_hostname_test.passed and test_results.duplicate_public_hostname_test.passed and test_results.valid_internal_domain_test.passed and test_results.valid_public_domain_test.passed and test_results.valid_simple_test.passed and test_results.valid_two_level_test.passed and test_results.invalid_consecutive_dots_test.passed and test_results.invalid_hyphen_start_test.passed and test_results.invalid_hyphen_end_test.passed and test_results.invalid_tld_test.passed and test_results.invalid_leading_dot_test.passed and test_results.invalid_trailing_dot_test.passed and test_results.invalid_no_tld_test.passed and test_results.invalid_empty_label_test.passed

summary = {
    all_tests_passed = all_passed
    results = test_results
}
