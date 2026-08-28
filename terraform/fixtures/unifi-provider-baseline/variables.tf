variable "run_id" {
  description = "Unique lowercase identifier used to isolate every sandbox DNS name."
  type        = string

  validation {
    condition     = can(regex("^[a-z0-9][a-z0-9-]{4,30}[a-z0-9]$", var.run_id))
    error_message = "run_id must be 6-32 lowercase letters, digits, or hyphens and may not start or end with a hyphen."
  }
}

variable "site" {
  description = "UniFi site in which disposable records are created."
  type        = string
  default     = "default"
}

variable "a_record_count" {
  description = "Number of representative A records to create."
  type        = number
  default     = 64

  validation {
    condition     = var.a_record_count >= 1 && var.a_record_count <= 200 && floor(var.a_record_count) == var.a_record_count
    error_message = "a_record_count must be a whole number from 1 through 200."
  }
}

variable "cname_record_count" {
  description = "Number of representative CNAME records to create."
  type        = number
  default     = 64

  validation {
    condition     = var.cname_record_count >= 1 && var.cname_record_count <= 200 && floor(var.cname_record_count) == var.cname_record_count
    error_message = "cname_record_count must be a whole number from 1 through 200."
  }
}

variable "update_first_record" {
  description = "Switch the first A record to a second benign private address for update testing."
  type        = bool
  default     = false
}
