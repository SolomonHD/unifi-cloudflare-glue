## 1. Document Structure Setup

- [ ] 1.1 Create troubleshooting.md section headers (Quick Diagnostics, Common Errors By Component, Decision Trees, Diagnostics Commands, FAQ, Getting Help)
- [ ] 1.2 Add table of contents with anchor links to each major section

## 2. Error Reference Documentation

- [ ] 2.1 Document Dagger module errors (module not found, secret parameter error, container execution failed, function not found)
- [ ] 2.2 Document Terraform errors (backend initialization failed, state lock timeout, provider authentication failed)
- [ ] 2.3 Document KCL validation errors (MAC address format invalid, DNS loop detected, duplicate MAC address, schema validation failures)
- [ ] 2.4 Document UniFi Controller errors (TLS certificate verify failed, API key invalid, connection refused, timeout)
- [ ] 2.5 Document Cloudflare API errors (zone not found, insufficient permissions, tunnel name already exists, rate limit exceeded)
- [ ] 2.6 Ensure each error entry has Symptoms, Cause, Solution, and Prevention sections

## 3. Decision Trees

- [ ] 3.1 Create deployment failure decision tree (branching by stage: config generation, terraform init, terraform plan/apply)
- [ ] 3.2 Create authentication failure decision tree (UniFi, Cloudflare, state backend credentials)
- [ ] 3.3 Create state management issues decision tree (backend connectivity, lock issues, migration)
- [ ] 3.4 Add cross-references from decision tree terminal nodes to error reference sections

## 4. Diagnostics Commands

- [ ] 4.1 Document Dagger verification commands (dagger version, dagger call hello, module help)
- [ ] 4.2 Document Terraform verification commands (terraform version, terraform providers)
- [ ] 4.3 Document KCL verification commands (kcl version, kcl run main.k)
- [ ] 4.4 Document network connectivity tests (UniFi Controller, Cloudflare API)
- [ ] 4.5 Document state backend verification commands (S3, Azure, GCS examples)
- [ ] 4.6 Add expected output examples for each diagnostic command

## 5. FAQ Section

- [ ] 5.1 Add FAQ entry: How do I reset state?
- [ ] 5.2 Add FAQ entry: Can I use multiple tunnels per device?
- [ ] 5.3 Add FAQ entry: Why does DNS loop validation fail?
- [ ] 5.4 Add FAQ entry: How do I debug KCL schemas?
- [ ] 5.5 Add FAQ entry: What MAC address formats are accepted?
- [ ] 5.6 Add FAQ entry: How do I update provider credentials?
- [ ] 5.7 Add FAQ entry: Why is my tunnel not connecting?
- [ ] 5.8 Add FAQ entry: How do I force-unlock Terraform state?
- [ ] 5.9 Add FAQ entry: What Cloudflare permissions are required?
- [ ] 5.10 Add FAQ entry: How do I verify my configuration before deploying?

## 6. Cross-References and Navigation

- [ ] 6.1 Update docs/README.md index to include troubleshooting guide with description
- [ ] 6.2 Add troubleshooting link to main README.md Documentation section
- [ ] 6.3 Add "See Troubleshooting" links from security.md relevant sections
- [ ] 6.4 Add "See Troubleshooting" links from state-management.md relevant sections
- [ ] 6.5 Add "See Troubleshooting" links from dagger-reference.md relevant sections
- [ ] 6.6 Add "See Troubleshooting" links from getting-started.md relevant sections

## 7. Validation

- [ ] 7.1 Verify all internal documentation links resolve correctly
- [ ] 7.2 Verify all decision tree ASCII art renders correctly in markdown
- [ ] 7.3 Verify diagnostic commands are accurate and tested
- [ ] 7.4 Verify error messages match actual error output from tools
