# Cloudflare Schema Extensions
# Extends base schemas for Cloudflare Tunnel management

# Cloudflare Tunnel configuration
# Represents a single tunnel connected to a physical device
schema CloudflareTunnel:
    """Cloudflare Tunnel configuration"""
    name: str
    account_id: str
    # The tunnel token would be provided separately for security
    
    check:
        len(name) > 0, "Tunnel name cannot be empty"
        len(account_id) > 0, "Account ID cannot be empty"

# Ingress rule for Cloudflare Tunnel
# Defines how traffic routes to local services
schema CloudflareIngress:
    """Ingress rule for tunnel routing"""
    hostname: str
    service: str
    path_prefix?: str
    
    check:
        len(hostname) > 0, "Hostname cannot be empty"
        len(service) > 0, "Service cannot be empty"

# Cloudflare configuration container
# Holds all Cloudflare-specific configuration
schema CloudflareConfig:
    """Complete Cloudflare Tunnel configuration"""
    tunnel: CloudflareTunnel
    ingress_rules: [CloudflareIngress] = []
    catch_all_service?: str
