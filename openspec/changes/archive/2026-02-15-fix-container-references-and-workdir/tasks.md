## 1. Fix deploy_unifi() Function

- [x] 1.1 Add `using_persistent_state = state_dir is not None` boolean variable at the beginning of container setup logic
- [x] 1.2 Replace fragile string check `"/module" in str(ctr)` with explicit `using_persistent_state` boolean logic for workdir selection
- [x] 1.3 Fix container reference preservation after `terraform init` - reassign `ctr = ctr.with_exec(init_cmd)` then `_ = await ctr.stdout()`
- [x] 1.4 Fix container reference preservation after `terraform apply` - reassign `ctr = ctr.with_exec([...])` then `apply_result = await ctr.stdout()`
- [x] 1.5 Ensure proper intermediate awaiting for state directory copy operation using `_ = await ctr.stdout()` pattern

## 2. Fix deploy_cloudflare() Function

- [x] 2.1 Add `using_persistent_state = state_dir is not None` boolean variable at the beginning of container setup logic
- [x] 2.2 Replace fragile string check `"/module" in str(ctr)` with explicit `using_persistent_state` boolean logic for workdir selection
- [x] 2.3 Fix container reference preservation after `terraform init` - reassign `ctr = ctr.with_exec(init_cmd)` then `_ = await ctr.stdout()`
- [x] 2.4 Fix container reference preservation after `terraform apply` - reassign `ctr = ctr.with_exec([...])` then `apply_result = await ctr.stdout()`
- [x] 2.5 Ensure proper intermediate awaiting for state directory copy operation using `_ = await ctr.stdout()` pattern

## 3. Fix destroy() Function - Cloudflare Phase

- [x] 3.1 Add `using_persistent_state = state_dir is not None` boolean variable at the beginning of Cloudflare destroy container setup
- [x] 3.2 Replace fragile string check `"/module" in str(ctr)` with explicit `using_persistent_state` boolean logic for Cloudflare phase workdir selection
- [x] 3.3 Fix container reference preservation after Cloudflare `terraform init` - reassign and await properly
- [x] 3.4 Fix container reference preservation after Cloudflare `terraform destroy` - reassign and await properly
- [x] 3.5 Ensure proper intermediate awaiting for state directory copy operation in Cloudflare phase

## 4. Fix destroy() Function - UniFi Phase

- [x] 4.1 Add `using_persistent_state = state_dir is not None` boolean variable at the beginning of UniFi destroy container setup
- [x] 4.2 Replace fragile string check `"/module" in str(ctr)` with explicit `using_persistent_state` boolean logic for UniFi phase workdir selection
- [x] 4.3 Fix container reference preservation after UniFi `terraform init` - reassign and await properly
- [x] 4.4 Fix container reference preservation after UniFi `terraform destroy` - reassign and await properly
- [x] 4.5 Ensure proper intermediate awaiting for state directory copy operation in UniFi phase

## 5. Validation and Testing

- [x] 5.1 Verify no occurrences of `str(ctr)` remain in `deploy_unifi()` for logic decisions
- [x] 5.2 Verify no occurrences of `str(ctr)` remain in `deploy_cloudflare()` for logic decisions
- [x] 5.3 Verify no occurrences of `str(ctr)` remain in `destroy()` for logic decisions
- [x] 5.4 Run Dagger module validation (`dagger functions`)
- [ ] 5.5 Test `deploy_unifi()` with ephemeral state (no state_dir)
- [ ] 5.6 Test `deploy_unifi()` with persistent state (with state_dir)
- [ ] 5.7 Test `deploy_cloudflare()` with ephemeral state (no state_dir)
- [ ] 5.8 Test `deploy_cloudflare()` with persistent state (with state_dir)
- [ ] 5.9 Test `destroy()` with ephemeral state (no state_dir)
- [ ] 5.10 Test `destroy()` with persistent state (with state_dir)
- [ ] 5.11 Verify `terraform.tfstate` is accessible from preserved container after each operation
