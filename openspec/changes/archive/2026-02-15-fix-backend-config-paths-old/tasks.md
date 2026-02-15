## 1. Fix Backend Config Path in plan() Function

- [x] 1.1 Change line 1106 in `plan()` function: update mount path from `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`
- [x] 1.2 Change line 1201 in `plan()` function: update mount path from `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`

## 2. Fix Backend Config Path in get_tunnel_secrets() Function

- [x] 2.1 Change line 2821 in `get_tunnel_secrets()` function: update mount path from `/root/.terraform/backend.hcl` to `/root/.terraform/backend.tfbackend`

## 3. Verification

- [x] 3.1 Run `dagger functions` to verify the module loads correctly
- [x] 3.2 Verify all three changed lines now reference `/root/.terraform/backend.tfbackend`
- [x] 3.3 Review the code to confirm mount paths match reference paths in terraform init commands

## 4. Documentation Update (if needed)

- [x] 4.1 Check if any documentation references the old `.hcl` path
- [x] 4.2 Update documentation if necessary

**Note:** Documentation references to `.hcl` files are user-provided filenames (e.g., `s3-backend.hcl`), not internal mount paths. No changes needed.
