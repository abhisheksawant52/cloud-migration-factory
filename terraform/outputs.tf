output "artifact_bucket_name" {
  description = "Name of the S3 bucket storing inventory and plan artifacts."
  value       = module.state_store.artifact_bucket_name
}

output "artifact_bucket_arn" {
  description = "ARN of the artifact S3 bucket."
  value       = module.state_store.artifact_bucket_arn
}

output "state_table_name" {
  description = "Name of the DynamoDB table storing migration task state."
  value       = module.state_store.state_table_name
}

output "state_table_arn" {
  description = "ARN of the migration state DynamoDB table."
  value       = module.state_store.state_table_arn
}

output "factory_role_arn" {
  description = "ARN of the IAM role used by the migration factory."
  value       = aws_iam_role.factory.arn
}
