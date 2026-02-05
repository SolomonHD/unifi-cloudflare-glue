#!/bin/bash
#
# Development Environment Deployment Script
#
# This script deploys infrastructure for development using ephemeral state.
# No state is persisted between runs - perfect for rapid iteration.
#
# Usage:
#   ./deploy.sh           # Deploy with .env file
#   ./deploy.sh --plan    # Only show plan, don't apply
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# =============================================================================
# Load Environment Variables
# =============================================================================

if [ -f .env ]; then
    echo -e "${GREEN}Loading environment from .env${NC}"
    export $(grep -v '^#' .env | xargs)
else
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Please copy .env.example to .env and fill in your credentials:"
    echo "  cp .env.example .env"
    exit 1
fi

# =============================================================================
# Validate Required Variables
# =============================================================================

if [ -z "$UNIFI_HOST" ] || [ -z "$CF_TOKEN" ] || [ -z "$CF_ACCOUNT_ID" ] || [ -z "$CF_ZONE_NAME" ]; then
    echo -e "${RED}Error: Missing required environment variables${NC}"
    echo "Please ensure .env contains:"
    echo "  - UNIFI_HOST"
    echo "  - CF_TOKEN"
    echo "  - CF_ACCOUNT_ID"
    echo "  - CF_ZONE_NAME"
    exit 1
fi

# Determine UniFi credentials
if [ -n "$UNIFI_API_KEY" ]; then
    UNIFI_CREDENTIALS="--unifi-api-key=env:UNIFI_API_KEY"
    echo -e "${GREEN}Using UniFi API Key authentication${NC}"
elif [ -n "$UNIFI_USERNAME" ] && [ -n "$UNIFI_PASSWORD" ]; then
    UNIFI_CREDENTIALS="--unifi-username=env:UNIFI_USERNAME --unifi-password=env:UNIFI_PASSWORD"
    echo -e "${YELLOW}Using UniFi username/password authentication (consider upgrading to API Key)${NC}"
else
    echo -e "${RED}Error: No UniFi credentials found${NC}"
    echo "Please set either UNIFI_API_KEY or UNIFI_USERNAME/UNIFI_PASSWORD in .env"
    exit 1
fi

# Module version (default to v0.3.2)
MODULE_VERSION="${MODULE_VERSION:-v0.3.2}"

# =============================================================================
# Pre-deployment Checks
# =============================================================================

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Development Environment Deployment    ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Configuration:${NC}"
echo "  UniFi Host: $UNIFI_HOST"
echo "  Zone: $CF_ZONE_NAME"
echo "  Module: $MODULE_VERSION"
echo "  State: Ephemeral (no persistence)"
echo ""

# Check for dagger
if ! command -v dagger &> /dev/null; then
    echo -e "${RED}Error: dagger command not found${NC}"
    echo "Please install Dagger: https://docs.dagger.io/install"
    exit 1
fi

# Check KCL configuration
echo -e "${GREEN}Validating KCL configuration...${NC}"
if ! kcl run kcl/main.k > /dev/null 2>&1; then
    echo -e "${YELLOW}Warning: KCL validation failed. Attempting to download dependencies...${NC}"
    kcl mod update
    if ! kcl run kcl/main.k > /dev/null 2>&1; then
        echo -e "${RED}Error: KCL validation failed. Please check your configuration.${NC}"
        exit 1
    fi
fi
echo -e "${GREEN}KCL configuration is valid${NC}"
echo ""

# =============================================================================
# Deployment
# =============================================================================

if [ "$1" == "--plan" ]; then
    echo -e "${GREEN}Running plan only (no changes will be made)...${NC}"
    dagger call -m "github.com/SolomonHD/unifi-cloudflare-glue@$MODULE_VERSION" plan \
        --kcl-source=./kcl \
        --unifi-url="https://$UNIFI_HOST:$UNIFI_PORT" \
        $UNIFI_CREDENTIALS \
        --cloudflare-token=env:CF_TOKEN \
        --cloudflare-account-id="$CF_ACCOUNT_ID" \
        --zone-name="$CF_ZONE_NAME" \
        export --path=./plan-output
    echo ""
    echo -e "${GREEN}Plan saved to ./plan-output/${NC}"
else
    echo -e "${GREEN}Deploying infrastructure...${NC}"
    echo -e "${YELLOW}Note: This will create ephemeral state (no persistence)${NC}"
    echo ""
    
    dagger call -m "github.com/SolomonHD/unifi-cloudflare-glue@$MODULE_VERSION" deploy \
        --kcl-source=./kcl \
        --unifi-url="https://$UNIFI_HOST:$UNIFI_PORT" \
        $UNIFI_CREDENTIALS \
        --cloudflare-token=env:CF_TOKEN \
        --cloudflare-account-id="$CF_ACCOUNT_ID" \
        --zone-name="$CF_ZONE_NAME"
    
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Deployment Complete!                  ${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo -e "${YELLOW}Important:${NC}"
    echo "  - State is ephemeral and will be lost when the container exits"
    echo "  - To destroy: ./destroy.sh"
    echo "  - To see changes: ./deploy.sh --plan"
    echo ""
    echo -e "${YELLOW}Next Steps:${NC}"
    echo "  1. Configure cloudflared on your device"
    echo "  2. Test internal DNS: nslookup dev-app.internal.lan"
    echo "  3. Test external access: https://dev.$CF_ZONE_NAME"
fi