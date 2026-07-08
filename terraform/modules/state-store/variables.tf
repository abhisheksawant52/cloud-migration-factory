variable "name_prefix" {
  description = "Prefix applied to created resource names."
  type        = string
}

variable "artifact_bucket_name" {
  description = "Globally unique S3 bucket name for inventory and plan artifacts."
  type        = string
}

variable "force_destroy" {
  description = "Allow Terraform to delete a non-empty bucket on destroy."
  type        = bool
  default     = false
}

variable "read_capacity" {
  description = "Provisioned read capacity for the state table."
  type        = number
  default     = 5
}

variable "write_capacity" {
  description = "Provisioned write capacity for the state table."
  type        = number
  default     = 5
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
