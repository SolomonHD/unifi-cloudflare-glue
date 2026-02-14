## ADDED Requirements

### Requirement: Domain syntax validation function
The system SHALL provide an `is_valid_domain` lambda function that validates domain names according to RFC 1123 rules.

#### Scenario: Valid internal domain passes validation
- **WHEN** user provides `local_service_url = "http://jellyfin.internal.lan:8096"`
- **THEN** the domain validation passes because `internal.lan` is a valid domain

#### Scenario: Valid public domain passes validation
- **WHEN** user provides `local_service_url = "http://jellyfin.mycompany.com:8096"`
- **THEN** the domain validation passes because `mycompany.com` is a valid domain

#### Scenario: Invalid domain with consecutive dots fails
- **WHEN** user provides `local_service_url = "http://invalid..domain:8096"`
- **THEN** the domain validation fails with a syntax error

#### Scenario: Invalid domain starting with hyphen fails
- **WHEN** user provides `local_service_url = "http://-invalid.com:8096"`
- **THEN** the domain validation fails because labels cannot start with hyphens

#### Scenario: Invalid domain with single-character TLD fails
- **WHEN** user provides `local_service_url = "http://example.a:8096"`
- **THEN** the domain validation fails because TLD must be at least 2 characters

### Requirement: Hostname extraction from URL
The validation function SHALL extract the hostname from a URL by removing protocol, port, and path components.

#### Scenario: HTTP URL with port
- **WHEN** validating `http://server.internal.lan:8080/path`
- **THEN** the extracted hostname is `server.internal.lan`

#### Scenario: HTTPS URL without port
- **WHEN** validating `https://secure.example.com/api`
- **THEN** the extracted hostname is `secure.example.com`

#### Scenario: URL with no path
- **WHEN** validating `http://simple.local`
- **THEN** the extracted hostname is `simple.local`

### Requirement: RFC 1123 label validation
Each label in the hostname SHALL conform to RFC 1123: 1-63 characters, starting and ending with alphanumeric, with hyphens allowed internally.

#### Scenario: Valid label with hyphen
- **WHEN** validating `my-server.internal.lan`
- **THEN** validation passes because `my-server` is a valid label

#### Scenario: Invalid label starting with hyphen
- **WHEN** validating `-server.internal.lan`
- **THEN** validation fails because labels cannot start with hyphens

#### Scenario: Invalid label ending with hyphen
- **WHEN** validating `server-.internal.lan`
- **THEN** validation fails because labels cannot end with hyphens

#### Scenario: Invalid label with underscore
- **WHEN** validating `my_server.internal.lan`
- **THEN** validation fails because underscores are not valid in hostnames

#### Scenario: Label exceeding 63 characters
- **WHEN** validating a label with 64+ characters
- **THEN** validation fails because labels must be 1-63 characters

### Requirement: TLD minimum length
The top-level domain (TLD) SHALL be at least 2 characters long.

#### Scenario: Valid two-character TLD
- **WHEN** validating `server.example.io`
- **THEN** validation passes because `io` is at least 2 characters

#### Scenario: Invalid single-character TLD
- **WHEN** validating `server.example.a`
- **THEN** validation fails because TLD must be at least 2 characters

### Requirement: Clear validation error messages
The system SHALL provide clear error messages indicating why domain validation failed.

#### Scenario: Error message for invalid characters
- **WHEN** domain contains invalid characters
- **THEN** error message includes "invalid characters in domain"

#### Scenario: Error message for label starting with hyphen
- **WHEN** a label starts with hyphen
- **THEN** error message includes "label cannot start with hyphen"

#### Scenario: Error message for consecutive dots
- **WHEN** domain contains consecutive dots
- **THEN** error message includes "consecutive dots not allowed"
