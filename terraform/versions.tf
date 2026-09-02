terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.62"
    }
  }

  # Remote state backend. Configure per environment with a partial backend
  # config, e.g. `terraform init -backend-config=environments/dev/backend.hcl`.
  # backend "s3" {
  #   bucket         = "migration-factory-tfstate"
  #   key            = "cloud-migration-factory/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "migration-factory-tflock"
  #   encrypt        = true
  # }
}
