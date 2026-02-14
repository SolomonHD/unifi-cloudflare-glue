## 1. Implement Domain Syntax Validation Lambda

- [x] 1.1 Create `is_valid_domain` lambda function in `kcl/schemas/cloudflare.k`
- [x] 1.2 Implement hostname extraction logic (remove protocol, port, path)
- [x] 1.3 Implement RFC 1123 label validation (1-63 chars, alphanumeric start/end, hyphens allowed internally)
- [x] 1.4 Implement TLD minimum length check (2+ characters)
- [x] 1.5 Implement invalid character detection (alphanumeric, hyphens, dots only)
- [x] 1.6 Implement consecutive dots check
- [x] 1.7 Implement leading/trailing dots check

## 2. Update TunnelService Schema

- [x] 2.1 Replace `is_internal_domain` call with `is_valid_domain` in check block
- [x] 2.2 Update error message to reflect syntax validation
- [x] 2.3 Update docstring for `local_service_url` attribute
- [x] 2.4 Remove or update comments referencing internal domain suffixes

## 3. Clean Up Old Validation

- [x] 3.1 Remove `is_internal_domain` lambda function (no longer needed)
- [x] 3.2 Remove hardcoded suffix list from code

## 4. Add Test Cases

- [x] 4.1 Add test case: valid internal domain (`.internal.lan`)
- [x] 4.2 Add test case: valid public domain (`.mycompany.com`)
- [x] 4.3 Add test case: invalid domain with consecutive dots
- [x] 4.4 Add test case: invalid domain starting with hyphen
- [x] 4.5 Add test case: invalid domain with single-character TLD
- [x] 4.6 Add test case: invalid domain with underscore
- [x] 4.7 Add test case: label exceeding 63 characters
- [x] 4.8 Verify existing test cases still pass

## 5. Validation and Verification

- [x] 5.1 Run `kcl kcl/test_validation.k` to verify all tests pass
- [x] 5.2 Run `kcl kcl/test_cloudflare.k` to verify Cloudflare schema tests pass
- [x] 5.3 Verify existing example configurations still validate correctly
- [x] 5.4 Test with new domain formats (e.g., `mycompany.com`)

## 6. Documentation Updates

- [x] 6.1 Update `kcl/README.md` if it references internal domain requirements
- [x] 6.2 Update `kcl/schemas/cloudflare.k` header comments
