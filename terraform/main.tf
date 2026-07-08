locals {
  name = "${var.name_prefix}-${var.environment}"
}

data "aws_caller_identity" "current" {}

# S3 bucket for inventory/plan artifacts + DynamoDB table for migration state.
module "state_store" {
  source = "./modules/state-store"

  name_prefix          = local.name
  artifact_bucket_name = var.artifact_bucket_name
  force_destroy        = var.force_destroy_artifacts
  read_capacity        = var.state_table_read_capacity
  write_capacity       = var.state_table_write_capacity
  tags                 = var.tags
}

# IAM role assumed by the migration factory to read/write artifacts and state.
data "aws_iam_policy_document" "assume_role" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]

    principals {
      type        = "AWS"
      identifiers = ["arn:aws:iam::${data.aws_caller_identity.current.account_id}:root"]
    }
  }
}

data "aws_iam_policy_document" "factory" {
  statement {
    sid    = "ArtifactAccess"
    effect = "Allow"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:ListBucket",
    ]
    resources = [
      module.state_store.artifact_bucket_arn,
      "${module.state_store.artifact_bucket_arn}/*",
    ]
  }

  statement {
    sid    = "StateAccess"
    effect = "Allow"
    actions = [
      "dynamodb:GetItem",
      "dynamodb:PutItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
      "dynamodb:Scan",
    ]
    resources = [module.state_store.state_table_arn]
  }
}

resource "aws_iam_role" "factory" {
  name               = "${local.name}-role"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "factory" {
  name   = "${local.name}-policy"
  role   = aws_iam_role.factory.id
  policy = data.aws_iam_policy_document.factory.json
}
