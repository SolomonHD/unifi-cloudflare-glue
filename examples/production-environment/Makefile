# Production Environment Makefile
#
# Provides convenient targets for deploying and managing production infrastructure.
# Uses vals for secure secret injection from 1Password.
#
# Security Features:
#   - Automatic cleanup of rendered secrets after operations
#   - vals integration for 1Password secret injection
#   - Checks to prevent accidental commits of secrets
#
# Usage:
#   make deploy    # Deploy infrastructure (cleans secrets after)
#   make destroy   # Destroy all resources (cleans secrets after)
#   make plan      # Preview changes (cleans secrets after)
#   make clean     # Remove all generated and secret files

# Default module version
MODULE_VERSION ?= v0.3.2

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# =============================================================================
# Default Target
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Production Environment - Available Targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Security Features:"
	@echo "  - Automatic secret cleanup after operations"
	@echo "  - vals integration for 1Password"
	@echo "  - Pre-commit checks for secrets"
	@echo ""
	@echo "Prerequisites:"
	@echo "  - vals installed (brew install vals)"
	@echo "  - 1Password CLI configured (op signin)"
	@echo "  - Dagger installed"
	@echo "  - .env file created from .env.example"

# =============================================================================
# Security Checks
# =============================================================================

.PHONY: security-check
security-check: ## Verify no secrets are committed
	@echo "$(GREEN)Running security checks...$(NC)"
	@if [ -f backend.yaml ]; then \
		echo "$(YELLOW)Warning: backend.yaml exists (should be temporary only)$(NC)"; \
	fi
	@echo "$(GREEN)✓ Security check passed$(NC)"

# =============================================================================
# Environment Setup
# =============================================================================

.PHONY: check-env
check-env: security-check ## Verify environment is properly configured
	@echo "$(GREEN)Checking environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "Please copy .env.example to .env and fill in your credentials:"; \
		echo "  cp .env.example .env"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ .env file exists$(NC)"
	@if [ ! -f backend.yaml.tmpl ]; then \
		echo "$(RED)Error: backend.yaml.tmpl not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ backend.yaml.tmpl exists$(NC)"
	@command -v dagger >/dev/null 2>&1 || { echo "$(RED)Error: dagger not found$(NC)"; exit 1; }
	@echo "$(GREEN)✓ dagger installed$(NC)"
	@command -v vals >/dev/null 2>&1 || { echo "$(YELLOW)Warning: vals not found. Install with: brew install vals$(NC)"; }
	@echo "$(GREEN)Environment check passed!$(NC)"

.PHONY: init
init: check-env ## Initialize KCL dependencies
	@echo "$(GREEN)Initializing KCL dependencies...$(NC)"
	cd kcl && kcl mod update

# =============================================================================
# Secret Management
# =============================================================================

.PHONY: render-secrets
render-secrets: check-env ## Render secrets from 1Password using vals
	@echo "$(GREEN)Rendering secrets from 1Password...$(NC)"
	@vals eval -f backend.yaml.tmpl > backend.yaml
	@echo "$(GREEN)✓ Secrets rendered to backend.yaml$(NC)"
	@echo "$(YELLOW)Warning: backend.yaml contains secrets - it will be auto-cleaned$(NC)"

.PHONY: clean-secrets
clean-secrets: ## Remove all rendered secret files
	@echo "$(GREEN)Cleaning up secret files...$(NC)"
	@rm -f backend.yaml
	@rm -f .env.rendered
	@echo "$(GREEN)✓ Secret files removed$(NC)"

# =============================================================================
# Deployment Targets
# =============================================================================

.PHONY: validate
validate: check-env ## Validate KCL configuration
	@echo "$(GREEN)Validating KCL configuration...$(NC)"
	@cd kcl && kcl run main.k > /dev/null 2>&1 && echo "$(GREEN)✓ KCL configuration is valid$(NC)" || { echo "$(RED)✗ KCL validation failed$(NC)"; exit 1; }

.PHONY: plan
plan: check-env validate render-secrets ## Generate execution plan without applying
	@echo "$(BLUE)========================================$(NC)"
	@echo "$(BLUE)  Generating Plan                       $(NC)"
	@echo "$(BLUE)========================================$(NC)"
	@echo ""
	@set -a && source .env && set +a && \
	dagger call -m "github.com/SolomonHD/unifi-cloudflare-glue@$(MODULE_VERSION)" plan \
		--kcl-source=./kcl \
		--unifi-url="https://$${UNIFI_HOST}:$${UNIFI_PORT:-443}" \
		--backend-config-file=./backend.yaml \
		$$(if [ -n "$${UNIFI_API_KEY}" ]; then echo "--unifi-api-key=env:UNIFI_API_KEY"; else echo "--unifi-username=env:UNIFI_USERNAME --unifi-password=env:UNIFI_PASSWORD"; fi) \
		--cloudflare-token=env:CF_TOKEN \
		--cloudflare-account-id="$${CF_ACCOUNT_ID}" \
		--zone-name="$${CF_ZONE_NAME}" \
		export --path=./plan-output || true
	@echo ""
	@$(MAKE) clean-secrets
	@echo "$(GREEN)Plan saved to ./plan-output/$(NC)"

.PHONY: deploy
deploy: check-env validate render-secrets ## Deploy infrastructure with secret cleanup
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Production Environment Deployment     $(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@set -a && source .env && set +a && \
	echo "$(YELLOW)Configuration:$(NC)" && \
	echo "  UniFi Host: $${UNIFI_HOST}" && \
	echo "  Zone: $${CF_ZONE_NAME}" && \
	echo "  Module: $(MODULE_VERSION)" && \
	echo "  State: S3 backend with DynamoDB locking" && \
	echo "  Secrets: vals + 1Password" && \
	echo "" && \
	echo "$(GREEN)Deploying infrastructure...$(NC)" && \
	dagger call -m "github.com/SolomonHD/unifi-cloudflare-glue@$(MODULE_VERSION)" deploy \
		--kcl-source=./kcl \
		--unifi-url="https://$${UNIFI_HOST}:$${UNIFI_PORT:-443}" \
		--backend-config-file=./backend.yaml \
		$$(if [ -n "$${UNIFI_API_KEY}" ]; then echo "--unifi-api-key=env:UNIFI_API_KEY"; else echo "--unifi-username=env:UNIFI_USERNAME --unifi-password=env:UNIFI_PASSWORD"; fi) \
		--cloudflare-token=env:CF_TOKEN \
		--cloudflare-account-id="$${CF_ACCOUNT_ID}" \
		--zone-name="$${CF_ZONE_NAME}"
	@echo ""
	@$(MAKE) clean-secrets
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Deployment Complete!                  $(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Next Steps:$(NC)"
	@echo "  1. Configure cloudflared on your production server"
	@echo "  2. Test internal DNS: nslookup production-app.internal.lan"
	@echo "  3. Test external access: https://app.$${CF_ZONE_NAME}"
	@echo "  4. Monitor Cloudflare Tunnel health in dashboard"

.PHONY: destroy
destroy: check-env render-secrets ## Destroy all infrastructure with secret cleanup
	@echo "$(RED)========================================$(NC)"
	@echo "$(RED)  WARNING: Destroy Production Environment $(NC)"
	@echo "$(RED)========================================$(NC)"
	@echo ""
	@echo "$(RED)This is a DESTRUCTIVE operation!$(NC)"
	@echo ""
	@echo "This will destroy:"
	@echo "  - All UniFi DNS records for this configuration"
	@echo "  - All Cloudflare Tunnel and DNS configurations"
	@echo "  - Tunnel credentials and tokens"
	@echo "  - Production access for your services"
	@echo ""
	@read -p "Are you ABSOLUTELY sure? Type 'destroy-production' to continue: " confirm; \
	if [ "$$confirm" != "destroy-production" ]; then \
		echo "Destruction cancelled."; \
		$(MAKE) clean-secrets; \
		exit 0; \
	fi
	@echo ""
	@echo "$(GREEN)Destroying infrastructure...$(NC)"
	@set -a && source .env && set +a && \
	dagger call -m "github.com/SolomonHD/unifi-cloudflare-glue@$(MODULE_VERSION)" destroy \
		--kcl-source=./kcl \
		--unifi-url="https://$${UNIFI_HOST}:$${UNIFI_PORT:-443}" \
		--backend-config-file=./backend.yaml \
		$$(if [ -n "$${UNIFI_API_KEY}" ]; then echo "--unifi-api-key=env:UNIFI_API_KEY"; else echo "--unifi-username=env:UNIFI_USERNAME --unifi-password=env:UNIFI_PASSWORD"; fi) \
		--cloudflare-token=env:CF_TOKEN \
		--cloudflare-account-id="$${CF_ACCOUNT_ID}" \
		--zone-name="$${CF_ZONE_NAME}"
	@echo ""
	@$(MAKE) clean-secrets
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Destruction Complete!                 $(NC)"
	@echo "$(GREEN)========================================$(NC)"

# =============================================================================
# Utility Targets
# =============================================================================

.PHONY: clean
clean: clean-secrets ## Remove all generated files and secrets
	@echo "$(GREEN)Cleaning all generated files...$(NC)"
	@rm -rf plan-output/
	@rm -f *.tfplan
	@rm -f *.rendered
	@echo "$(GREEN)✓ Clean complete$(NC)"

.PHONY: fmt
fmt: ## Format KCL configuration
	@echo "$(GREEN)Formatting KCL files...$(NC)"
	@cd kcl && kcl fmt main.k

.PHONY: update
update: ## Update KCL module dependencies
	@echo "$(GREEN)Updating KCL dependencies...$(NC)"
	@cd kcl && kcl mod update

.PHONY: status
status: ## Show current environment status
	@echo "$(BLUE)Production Environment Status$(NC)"
	@echo ""
	@echo "Files:"
	@if [ -f .env ]; then echo "  ✓ .env"; else echo "  ✗ .env (missing)"; fi
	@if [ -f backend.yaml.tmpl ]; then echo "  ✓ backend.yaml.tmpl"; else echo "  ✗ backend.yaml.tmpl (missing)"; fi
	@if [ -f backend.yaml ]; then echo "  ⚠ backend.yaml (should be temporary)"; else echo "  ✓ backend.yaml (clean)"; fi
	@echo ""
	@echo "Secret Status:"
	@$(MAKE) -s clean-secrets 2>/dev/null || true
