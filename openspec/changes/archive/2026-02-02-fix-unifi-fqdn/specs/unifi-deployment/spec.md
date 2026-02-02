# Spec: UniFi Deployment

## MODIFIED Requirements

### Requirement: UniFi DNS A-Records Must Use Full FQDN

The UniFi DNS module SHALL create A-records with complete Fully Qualified Domain Names (FQDNs) by concatenating the hostname and domain fields from the device configuration.

**Status:** Modified (fixing incomplete hostname bug)

**Rationale:** DNS A-records should be created with full domain names to ensure proper resolution and consistency with CNAME records. The current implementation creates incomplete records with only the hostname portion.

#### Scenario: Create DNS A-Record with Full FQDN

Given:
- A device configuration containing `hostname` "test-server" and `domain` "internal.lan"
- The device's MAC address is found in the UniFi controller
- The `local.dns_records` map provides both `hostname` and `domain` fields

When:
- The Terraform module creates a UniFi DNS A-record resource

Then:
- The A-record `name` field SHALL be `"test-server.internal.lan"`
- The record SHALL be visible in the UniFi controller with the complete FQDN
- The pattern SHALL match the CNAME record implementation: `"${hostname}.${domain}"`

#### Scenario: Integration Test Creates Proper FQDN Records

Given:
- Integration test generates a random hostname like "test-14fqf"
- Test configuration specifies domain "sghd.io"
- The test device is known to the UniFi controller

When:
- `test_integration` Dagger function deploys the UniFi DNS module

Then:
- The UniFi DNS A-record SHALL be created with name "test-14fqf.sghd.io"
- The UniFi controller UI SHALL display the full FQDN in the Domain Name field
- The test success message SHALL show: "✓ Created UniFi DNS record: test-14fqf.sghd.io"

#### Scenario: FQDN Pattern Consistency Across Record Types

Given:
- The UniFi DNS module supports both A-records and CNAME records
- Both record types have access to `hostname` and `domain` fields

When:
- The module creates any DNS record (A or CNAME)

Then:
- The FQDN construction pattern SHALL be consistent: `"${hostname}.${domain}"`
- A-records SHALL use the same pattern as CNAME records (currently line 178 in main.tf)
- No DNS record type SHALL create incomplete hostnames without domains
