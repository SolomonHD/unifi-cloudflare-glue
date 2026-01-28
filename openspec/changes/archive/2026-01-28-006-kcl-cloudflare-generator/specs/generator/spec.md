## ADDED Requirements

### Requirement: Cloudflare Generator Function

The generator SHALL provide a `generate_cloudflare_config()` function that accepts a `CloudflareConfig` and returns a dictionary suitable for JSON serialization.

#### Scenario: Basic Generator Invocation
Given a valid `CloudflareConfig` instance with zone_name, account_id, and at least one tunnel
When `generate_cloudflare_config(config)` is called
Then it returns a dictionary with `zone_name`, `account_id`, and `tunnels` keys

#### Scenario: Empty Configuration
Given a `CloudflareConfig` with empty tunnels dictionary
When `generate_cloudflare_config(config)` is called
Then it returns `{"zone_name": "...", "account_id": "...", "tunnels": {}}`

### Requirement: Tunnel Keying by MAC Address

The generator SHALL key tunnels in the output dictionary by normalized MAC address.

#### Scenario: Single Tunnel Keying
Given a `CloudflareTunnel` with `mac_address = "aa:bb:cc:dd:ee:ff"`
When the tunnel is transformed
Then the output tunnels dictionary contains a key `"aa:bb:cc:dd:ee:ff"`

#### Scenario: MAC Normalization for Key
Given a `CloudflareTunnel` with `mac_address = "AA-BB-CC-DD-EE-FF"`
When the tunnel is transformed
Then the output tunnels dictionary key is `"aa:bb:cc:dd:ee:ff"` (normalized)

#### Scenario: Multiple Tunnels
Given a `CloudflareConfig` with two `CloudflareTunnel` objects with different MACs
When `generate_cloudflare_config()` is called
Then the output `tunnels` dictionary contains both tunnels keyed by their MACs

### Requirement: Service Distribution Filtering

The generator SHALL only include services where `distribution` is `"cloudflare_only"` or `"both"`.

#### Scenario: Cloudflare-Only Service
Given a service with `distribution = "cloudflare_only"`
When the tunnel is transformed
Then the service is included in the tunnel's services list

#### Scenario: Both Distribution Service
Given a service with `distribution = "both"`
When the tunnel is transformed
Then the service is included in the tunnel's services list

#### Scenario: UniFi-Only Service Exclusion
Given a service with `distribution = "unifi_only"`
When the tunnel is transformed
Then the service is NOT included in the tunnel's services list

### Requirement: Local Service URL Construction

The generator SHALL construct `local_service_url` from service protocol, hostname, and port.

#### Scenario: URL with Internal Hostname
Given a service with:
- `protocol = "http"`
- `internal_hostname = "jellyfin.internal.lan"`
- `port = 8096`
When the service is transformed
Then `local_service_url = "http://jellyfin.internal.lan:8096"`

#### Scenario: URL with HTTPS Protocol
Given a service with:
- `protocol = "https"`
- `internal_hostname = "nas.internal.lan"`
- `port = 443`
When the service is transformed
Then `local_service_url = "https://nas.internal.lan:443"`

#### Scenario: URL Fallback to Device Hostname
Given a service without `internal_hostname` on a device with:
- `friendly_hostname = "media-server"`
- internal domain = "internal.lan"
When the service is transformed
Then `local_service_url` uses `"media-server.internal.lan"` as hostname

### Requirement: Public Hostname Resolution

The generator SHALL resolve `public_hostname` for each service.

#### Scenario: Explicit Public Hostname
Given a service with `public_hostname = "media.example.com"`
When the service is transformed
Then the output contains `public_hostname = "media.example.com"`

#### Scenario: Generated Public Hostname
Given a service with:
- `name = "jellyfin"`
- No explicit `public_hostname`
- Zone name = "example.com"
When the service is transformed
Then `public_hostname = "jellyfin.example.com"`

#### Scenario: Zone Subdomain Validation
Given a service with `public_hostname = "media.other.com"`
And the CloudflareConfig zone_name = "example.com"
When validated
Then a warning is issued about zone mismatch

### Requirement: DNS Loop Prevention

The generator SHALL validate that `local_service_url` uses internal domains only to prevent DNS resolution loops.

#### Scenario: Valid Internal Domain
Given a `local_service_url = "http://jellyfin.internal.lan:8096"`
When validated for zone "example.com"
Then validation passes (URL does not contain zone name)

#### Scenario: Valid Local Domain
Given a `local_service_url = "http://server.local:8080"`
When validated
Then validation passes

#### Scenario: DNS Loop Detected
Given a `local_service_url = "http://jellyfin.example.com:8096"`
And zone_name = "example.com"
When validated
Then validation fails with error about DNS loop risk

#### Scenario: Zone in Hostname Rejected
Given a `local_service_url = "https://app.example.com:443"`
And zone_name = "example.com"
When validated
Then an error is raised: "local_service_url must not contain the public zone name"

### Requirement: Optional Field Handling

The generator SHALL handle optional fields gracefully.

#### Scenario: Missing no_tls_verify
Given a service without `no_tls_verify` specified
When transformed
Then the output uses the default value `false`

#### Scenario: Missing path_prefix
Given a service without `path_prefix`
When transformed
Then the output omits the `path_prefix` field (not included in JSON)

#### Scenario: Missing credentials_path
Given a tunnel without `credentials_path`
When transformed
Then the output omits the `credentials_path` field

### Requirement: JSON Output Format

The generator SHALL produce JSON that matches the Cloudflare Terraform module input schema.

#### Scenario: Valid JSON Structure
Given a valid `CloudflareConfig`
When `generate_cloudflare_config()` output is serialized to JSON
Then the JSON is valid and can be parsed

#### Scenario: Complete Output Structure
Given a `CloudflareConfig` with at least one tunnel
When output is generated
Then the JSON contains:
```json
{
  "zone_name": "example.com",
  "account_id": "xxx",
  "tunnels": {
    "aa:bb:cc:dd:ee:ff": {
      "tunnel_name": "tunnel-name",
      "services": [{
        "public_hostname": "app.example.com",
        "local_service_url": "http://app.internal.lan:8080",
        "no_tls_verify": false
      }]
    }
  }
}
```

### Requirement: Default no_tls_verify Inheritance

The generator SHALL support inheriting `default_no_tls_verify` from `CloudflareConfig`.

#### Scenario: Default Value Applied
Given a `CloudflareConfig` with `default_no_tls_verify = true`
And a service without explicit `no_tls_verify`
When the service is transformed
Then the output uses `no_tls_verify = true`

#### Scenario: Service Override
Given a `CloudflareConfig` with `default_no_tls_verify = true`
And a service with `no_tls_verify = false`
When the service is transformed
Then the output uses `no_tls_verify = false` (service overrides default)
