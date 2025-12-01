output "cognito_user_pool_id" {
  description = "Cognito User Pool ID"
  value       = aws_cognito_user_pool.main.id
}

output "cognito_user_pool_client_id" {
  description = "Cognito User Pool Client ID"
  value       = aws_cognito_user_pool_client.main.id
  sensitive   = false
}

output "cognito_user_pool_arn" {
  description = "Cognito User Pool ARN"
  value       = aws_cognito_user_pool.main.arn
}

output "s3_bucket_name" {
  description = "S3 bucket name for receipts"
  value       = aws_s3_bucket.receipts.id
}

output "s3_bucket_arn" {
  description = "S3 bucket ARN"
  value       = aws_s3_bucket.receipts.arn
}

output "dynamodb_table_name" {
  description = "DynamoDB table name for expenses"
  value       = aws_dynamodb_table.expenses.name
}

output "dynamodb_table_arn" {
  description = "DynamoDB table ARN"
  value       = aws_dynamodb_table.expenses.arn
}

output "api_gateway_url" {
  description = "API Gateway endpoint URL"
  value       = "${aws_api_gateway_stage.main.invoke_url}"
}

output "lambda_function_arn" {
  description = "Lambda function ARN for receipt processing"
  value       = aws_lambda_function.receipt_processor.arn
}

output "lambda_function_name" {
  description = "Lambda function name"
  value       = aws_lambda_function.receipt_processor.function_name
}

