provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "cloud-migration-factory"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}
