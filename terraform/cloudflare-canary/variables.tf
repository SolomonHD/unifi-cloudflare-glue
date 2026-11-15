variable "zone_id" {
  description = "Trusted existing solomonhd.ai zone ID; verified by a blocking precondition."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[0-9a-f]{32}$", var.zone_id))
    error_message = "A canonical Cloudflare zone ID is required."
  }
}

variable "run_prefix" {
  description = "Canonical gha-<unix>-<run-id>-<attempt> label, never truncated."
  type        = string
  nullable    = false

  validation {
    condition     = length(var.run_prefix) <= 63 && can(regex("^gha-[1-9][0-9]*-[1-9][0-9]*-[1-9][0-9]*$", var.run_prefix))
    error_message = "The run prefix must be a positive decimal canary identity of at most 63 characters."
  }
}

variable "txt_value" {
  description = "Non-secret marker, changed by the lifecycle's update phase."
  type        = string
  nullable    = false

  validation {
    condition     = can(regex("^[A-Za-z0-9_-]{1,128}$", var.txt_value))
    error_message = "Use a nonempty ASCII marker of at most 128 characters."
  }
}

variable "cname_target" {
  description = "Only reserved documentation targets or this run's sibling TXT name."
  type        = string
  nullable    = false

  validation {
    condition     = contains(["example.com", "example.org", "${var.run_prefix}.txt.ci.solomonhd.ai"], var.cname_target)
    error_message = "Use only the two documentation targets or the exact sibling TXT name."
  }
}
