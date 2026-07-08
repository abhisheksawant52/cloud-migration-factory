output "artifact_bucket_name" {
  description = "Name of the artifact S3 bucket."
  value       = aws_s3_bucket.artifacts.id
}

output "artifact_bucket_arn" {
  description = "ARN of the artifact S3 bucket."
  value       = aws_s3_bucket.artifacts.arn
}

output "state_table_name" {
  description = "Name of the migration state DynamoDB table."
  value       = aws_dynamodb_table.state.name
}

output "state_table_arn" {
  description = "ARN of the migration state DynamoDB table."
  value       = aws_dynamodb_table.state.arn
}
