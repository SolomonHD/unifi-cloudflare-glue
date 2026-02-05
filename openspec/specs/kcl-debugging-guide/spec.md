## ADDED Requirements

### Requirement: Syntax error diagnosis
The documentation SHALL provide systematic approach to diagnosing and fixing KCL syntax errors with line number interpretation.

#### Scenario: User encounters syntax error
- **WHEN** user runs kcl and receives syntax error
- **THEN** documentation explains how to interpret error line numbers and common syntax mistakes

#### Scenario: User fixes bracket mismatch
- **WHEN** user has unclosed schema or list
- **THEN** documentation shows how to identify mismatched brackets/braces and use editor bracket matching

#### Scenario: User corrects indentation errors
- **WHEN** user receives unexpected indentation error
- **THEN** documentation explains KCL indentation rules and how to fix inconsistent spacing

### Requirement: Type error diagnosis
The documentation SHALL provide approach to diagnosing type mismatches between schema definitions and configuration values.

#### Scenario: User encounters type mismatch
- **WHEN** user assigns wrong type to field
- **THEN** documentation explains how to identify expected vs actual type and provide correct value

#### Scenario: User fixes string/int confusion
- **WHEN** user provides string for integer field or vice versa
- **THEN** documentation shows common type errors and correct syntax (port: 8080 vs port: "8080")

#### Scenario: User resolves list/dict mismatch
- **WHEN** user provides single value where list expected or dict where list expected
- **THEN** documentation demonstrates correct list syntax [item1, item2] and dict syntax {key: value}

### Requirement: Validation error diagnosis
The documentation SHALL provide approach to interpreting check block failures and cross-provider validation errors.

#### Scenario: User encounters check block failure
- **WHEN** user receives validation error from check block
- **THEN** documentation shows how to read error message, identify violated constraint, and correct value

#### Scenario: User fixes MAC consistency error
- **WHEN** user has MAC in Cloudflare tunnel not present in UniFi devices
- **THEN** documentation explains error message, shows available MACs, and correction options

#### Scenario: User resolves hostname uniqueness error
- **WHEN** user has duplicate friendly_hostname values
- **THEN** documentation identifies conflicting hostnames and suggests unique naming strategy

#### Scenario: User fixes DNS loop error
- **WHEN** user uses public zone in local_service_url
- **THEN** documentation explains DNS loop consequence and shows correct internal hostname replacement

### Requirement: Generator error diagnosis
The documentation SHALL provide approach to debugging JSON generation failures and output validation.

#### Scenario: User encounters generator error
- **WHEN** user runs generator and receives runtime error
- **THEN** documentation shows how to isolate failing function and validate input data

#### Scenario: User debugs missing output
- **WHEN** user expects service in output but it's filtered
- **THEN** documentation explains distribution filtering logic and how to verify service inclusion criteria

#### Scenario: User validates generated JSON
- **WHEN** user wants to verify generator output correctness
- **THEN** documentation provides JSON validation commands and structure checks

### Requirement: Common mistake reference
The documentation SHALL catalog common configuration mistakes with recognition patterns and fixes.

#### Scenario: User references common mistakes
- **WHEN** user encounters unfamiliar error
- **THEN** documentation provides searchable list of errors with symptoms and solutions

#### Scenario: User avoids MAC format mistakes
- **WHEN** user reads common mistakes
- **THEN** documentation shows incorrect MAC formats and explains normalization

#### Scenario: User prevents distribution errors
- **WHEN** user configures service distribution
- **THEN** documentation lists common distribution mistakes (typos in enum values, wrong distribution for use case)

### Requirement: Step-by-step debugging workflow
The documentation SHALL provide ordered debugging workflow from syntax through validation to generation.

#### Scenario: User follows debugging workflow
- **WHEN** user has configuration errors
- **THEN** documentation provides step-by-step process: validate syntax first, then types, then validation rules, then generation

#### Scenario: User isolates error source
- **WHEN** user has multiple errors
- **THEN** documentation explains how to fix errors in order (syntax → types → validation) to reduce cascading failures

#### Scenario: User tests incrementally
- **WHEN** user adds new configuration
- **THEN** documentation recommends validating after each addition to isolate error source
