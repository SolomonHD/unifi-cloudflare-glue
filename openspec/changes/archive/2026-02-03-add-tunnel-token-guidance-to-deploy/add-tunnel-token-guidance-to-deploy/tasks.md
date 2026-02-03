## 1. Update deploy_cloudflare() Success Message

- [x] 1.1 Locate success message construction in [`deploy_cloudflare()`](../../src/main/main.py:563-569)
- [x] 1.2 Add visual separator line before guidance section
- [x] 1.3 Add "Next Step: Retrieve Tunnel Credentials" header
- [x] 1.4 Add Terraform output command example
- [x] 1.5 Build parameterized Dagger command with actual deployment values (account ID, zone name)
- [x] 1.6 Add conditional backend flags to Dagger command (backend-type, backend-config-file)
- [x] 1.7 Add conditional state-dir flag for persistent local state
- [x] 1.8 Add cloudflared service install command example
- [x] 1.9 Add link to example documentation
- [x] 1.10 Add closing visual separator line
- [x] 1.11 Preserve existing apply result output after guidance

## 2. Update deploy() Success Message

- [x] 2.1 Locate final summary section in [`deploy()`](../../src/main/main.py:725-741)
- [x] 2.2 Add conditional check for both UniFi and Cloudflare success
- [x] 2.3 Add visual separator line before guidance section (only if both succeed)
- [x] 2.4 Add "Next Step: Retrieve Tunnel Credentials" header
- [x] 2.5 Build parameterized Dagger command with `--source=./kcl` and deployment parameters
- [x] 2.6 Add conditional backend flags to Dagger command
- [x] 2.7 Add conditional state-dir flag if provided
- [x] 2.8 Add cloudflared service install command example
- [x] 2.9 Add link to example documentation
- [x] 2.10 Add closing visual separator line
- [x] 2.11 Verify guidance only appears in both-success case

## 3. Update Unit Tests

- [x] 3.1 Update [`deploy_cloudflare()`](../../src/main/main.py:422-571) success tests to expect new message format
- [x] 3.2 Add assertion for "Next Step: Retrieve Tunnel Credentials" in success message
- [x] 3.3 Add assertion for "dagger call get-tunnel-secrets" in success message
- [x] 3.4 Verify backend-specific command parameters appear in message (local vs remote)
- [x] 3.5 Verify state-dir flag appears when using persistent state
- [x] 3.6 Update [`deploy()`](../../src/main/main.py:574-742) success tests to expect guidance
- [x] 3.7 Verify guidance only appears when both deployments succeed
- [x] 3.8 Verify guidance does NOT appear when only UniFi succeeds
- [x] 3.9 Verify guidance does NOT appear when UniFi fails

## 4. Manual Testing

- [x] 4.1 Test [`deploy_cloudflare()`](../../src/main/main.py:422-571) with local backend, verify output format
- [x] 4.2 Test [`deploy_cloudflare()`](../../src/main/main.py:422-571) with remote backend, verify backend flags in command
- [x] 4.3 Test [`deploy_cloudflare()`](../../src/main/main.py:422-571) with persistent state dir, verify state-dir flag
- [x] 4.4 Test [`deploy()`](../../src/main/main.py:574-742) end-to-end with both phases succeeding
- [x] 4.5 Verify Dagger command parameters match actual deployment input
- [x] 4.6 Copy-paste generated Dagger command to verify it's executable
- [x] 4.7 Verify link to example documentation is correct

## 5. Documentation

- [x] 5.1 No external documentation updates needed (guidance is self-contained)
- [x] 5.2 Verify inline comments explain conditional guidance logic
