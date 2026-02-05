# Staging Environment Makefile
#
# Provides convenient targets for deploying and managing staging infrastructure.
# Uses S3 backend for state persistence and team collaboration.
#
# Usage:
#   make deploy    # Deploy infrastructure
#   make destroy   # Destroy all resources
#   make plan      # Preview changes
#   make clean     # Remove local generated files

# Default module version
MODULE_VERSION ?= v0.3.2

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m # No Color

# =============================================================================
# Default Target
# =============================================================================

.PHONY: help
help: ## Show this help message
	@echo "Staging Environment - Available Targets:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  $(GREEN)%-15s$(NC) %s\n", $$1, $$2}'
	@echo ""
	@echo "Prerequisites:"
	@echo "  - AWS credentials configured"
	@echo "  - Dagger installed"
	@echo "  - .env file created from .env.example"

# =============================================================================
# Environment Setup
# =============================================================================

.PHONY: check-env
check-env: ## Verify environment is properly configured
	@echo "$(GREEN)Checking environment...$(NC)"
	@if [ ! -f .env ]; then \
		echo "$(RED)Error: .env file not found$(NC)"; \
		echo "Please copy .env.example to .env and fill in your credentials:"; \
		echo "  cp .env.example .env"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ .env file exists$(NC)"
	@if [ ! -f backend.yaml ]; then \
		echo "$(RED)Error: backend.yaml not found$(NC)"; \
		exit 1; \
	fi
	@echo "$(GREEN)✓ backend.yaml exists$(NC)"
	@command -v dagger >/dev/null 2>&1 || { echo "$(RED)Error: dagger not found$(NC)"; exit 1; }
	@echo "$(GREEN)✓ dagger installed$(NC)"
	@echo "$(GREEN)Environment check passed!$(NC)"

.PHONY: init
init: check-env ## Initialize KCL dependencies
	@echo "$(GREEN)Initializing KCL dependencies...$(NC)"
	cd kcl && kcl mod update

# =============================================================================
# Deployment Targets
# =============================================================================

.PHONY: validate
validate: check-env ## Validate KCL configuration
	@echo "$(GREEN)Validating KCL configuration...$(NC)"
	@cd kcl && kcl run main.k > /dev/null 2>&1 && echo "$(GREEN)✓ KCL configuration is valid$(NC)" || { echo "$(RED)✗ KCL validation failed$(NC)"; exit 1; }

.PHONY: plan
plan: check-env validate ## Generate execution plan without applying
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Generating Plan                       $(NC)"
	@echo "$(GREEN)========================================$(NC)"
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
		export --path=./plan-output
	@echo ""
	@echo "$(GREEN)Plan saved to ./plan-output/$(NC)"

.PHONY: deploy
deploy: check-env validate ## Deploy infrastructure with S3 backend
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Staging Environment Deployment        $(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@set -a && source .env && set +a && \
	echo "$(YELLOW)Configuration:$(NC)" && \
	echo "  UniFi Host: $${UNIFI_HOST}" && \
	echo "  Zone: $${CF_ZONE_NAME}" && \
	echo "  Module: $(MODULE_VERSION)" && \
	echo "  State: S3 backend with lockfile" && \
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
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Deployment Complete!                  $(NC)"
	@echo "$(GREEN)========================================$(NC)"
	@echo ""
	@echo "$(YELLOW)Next Steps:$(NC)"
	@echo "  1. Configure cloudflared on your device"
	@echo "  2. Test internal DNS: nslookup staging-app.internal.lan"
	@echo "  3. Test external access: https://staging.$${CF_ZONE_NAME}"

.PHONY: destroy
destroy: check-env ## Destroy all infrastructure
	@echo "$(RED)========================================$(NC)"
	@echo "$(RED)  WARNING: Destroy Staging Environment  $(NC)"
	@echo "$(RED)========================================$(NC)"
	@echo ""
	@echo "This will destroy:"
	@echo "  - All UniFi DNS records for this configuration"
	@echo "  - All Cloudflare Tunnel and DNS configurations"
	@echo "  - Tunnel credentials and tokens"
	@echo ""
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "Destruction cancelled."; \
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
	@echo "$(GREEN)========================================$(NC)"
	@echo "$(GREEN)  Destruction Complete!                 $(NC)"
	@echo "$(GREEN)========================================$(NC)"

# =============================================================================
# Utility Targets
# =============================================================================

.PHONY: clean
clean: ## Remove local generated files
	@echo "$(GREEN)Cleaning local files...$(NC)"
	@rm -rf plan-output/
	@rm -f *.tfplan
	@echo "$(GREEN)✓ Clean complete$(NC)"

.PHONY: fmt
fmt: ## Format KCL configuration
	@echo "$(GREEN)Formatting KCL files...$(NC)"
	@cd kcl && kcl fmt main.k

.PHONY: update
update: ## Update KCL module dependencies
	@echo "$(GREEN)Updating KCL dependencies...$(NC)"
	@cd kcl && kcl mod update
