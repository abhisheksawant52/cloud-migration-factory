variable "aws_region" {
  description = "AWS region for the migration factory's deployment infrastructure."
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Deployment environment name (e.g. dev, prod)."
  type        = string
  default     = "dev"
}

variable "name_prefix" {
  description = "Prefix applied to all created resource names."
  type        = string
  default     = "migration-factory"
}

variable "artifact_bucket_name" {
  description = "Globally unique S3 bucket name for inventory and plan artifacts."
  type        = string
}

variable "force_destroy_artifacts" {
  description = "Allow Terraform to delete a non-empty artifact bucket on destroy."
  type        = bool
  default     = false
}

variable "state_table_read_capacity" {
  description = "Provisioned read capacity for the migration state table."
  type        = number
  default     = 5
}

variable "state_table_write_capacity" {
  description = "Provisioned write capacity for the migration state table."
  type        = number
  default     = 5
}

variable "tags" {
  description = "Additional tags applied to all resources."
  type        = map(string)
  default     = {}
}
