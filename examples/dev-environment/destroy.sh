#!/bin/bash
#
# Development Environment Destroy Script
#
# This script destroys all infrastructure created by deploy.sh.
# Uses ephemeral state - no backend configuration needed.
#
# Usage:
#   ./destroy.sh          # Destroy all resources
#   ./destroy.sh --force  # Skip confirmation prompt
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
    echo "Please ensure .env contains all required variables"
    exit 1
fi

# Determine UniFi credentials
if [ -n "$UNIFI_API_KEY" ]; then
    UNIFI_CREDENTIALS="--unifi-api-key=env:UNIFI_API_KEY"
else
    UNIFI_CREDENTIALS="--unifi-username=env:UNIFI_USERNAME --unifi-password=env:UNIFI_PASSWORD"
fi

# Module version
MODULE_VERSION="${MODULE_VERSION:-v0.3.2}"

# =============================================================================
# Confirmation
# =============================================================================

if [ "$1" != "--force" ]; then
    echo -e "${RED}========================================${NC}"
    echo -e "${RED}  WARNING: Destroy Development Environment  ${NC}"
    echo -e "${RED}========================================${NC}"
    echo ""
    echo "This will destroy:"
    echo "  - All UniFi DNS records for this configuration"
    echo "  - All Cloudflare Tunnel and DNS configurations"
    echo "  - Tunnel credentials and tokens"
    echo ""
    echo -e "${YELLOW}Zone: $CF_ZONE_NAME${NC}"
    echo ""
    read -p "Are you sure you want to continue? (yes/no): " confirm
    
    if [ "$confirm" != "yes" ]; then
        echo "Destruction cancelled."
        exit 0
    fi
fi

# =============================================================================
# Destruction
# =============================================================================

echo ""
echo -e "${GREEN}Destroying infrastructure...${NC}"
echo ""

dagger call -m "github.com/SolomonHD/unifi-cloudflare-glue@$MODULE_VERSION" destroy \
    --kcl-source=./kcl \
    --unifi-url="https://$UNIFI_HOST:$UNIFI_PORT" \
    $UNIFI_CREDENTIALS \
    --cloudflare-token=env:CF_TOKEN \
    --cloudflare-account-id="$CF_ACCOUNT_ID" \
    --zone-name="$CF_ZONE_NAME"

echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Destruction Complete!                 ${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "${YELLOW}Note:${NC}"
echo "  All resources have been destroyed."
echo "  State was ephemeral - no cleanup needed."
echo ""
echo -e "${YELLOW}Next Steps:${NC}"
echo "  - Remove cloudflared from your device if no longer needed"
echo "  - Clear DNS cache: sudo systemd-resolve --flush-caches (Linux)"
echo "  - Or: sudo killall -HUP mDNSResponder (macOS)"