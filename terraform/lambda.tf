# Lambda function for receipt processing
resource "aws_lambda_function" "receipt_processor" {
  filename         = "${path.module}/../backend/lambda_functions/receipt_processor.zip"
  function_name    = "${var.project_name}-${var.environment}-receipt-processor"
  role             = aws_iam_role.lambda_role.arn
  handler          = "receipt_processor.lambda_handler"
  runtime          = var.lambda_runtime
  timeout          = var.lambda_timeout
  memory_size      = var.lambda_memory_size

  environment {
    variables = {
      EXPENSES_TABLE_NAME  = aws_dynamodb_table.expenses.name
      RECEIPTS_TABLE_NAME  = aws_dynamodb_table.receipts.name
      S3_BUCKET_NAME       = aws_s3_bucket.receipts.id
      ENABLE_TEXTRACT      = var.enable_textract
    }
  }

  depends_on = [
    aws_iam_role_policy.lambda_policy,
    aws_cloudwatch_log_group.lambda_logs
  ]

  tags = {
    Name = "${var.project_name}-${var.environment}-receipt-processor"
  }
}

# CloudWatch Log Group for Lambda
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/${var.project_name}-${var.environment}-receipt-processor"
  retention_in_days = 14

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-logs"
  }
}

# Lambda Permission for S3 to invoke Lambda
resource "aws_lambda_permission" "s3_invoke" {
  statement_id  = "AllowExecutionFromS3Bucket"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.receipt_processor.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.receipts.arn
}

# Lambda Permission for API Gateway to invoke Lambda
resource "aws_lambda_permission" "api_gateway_invoke" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.receipt_processor.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.main.execution_arn}/*/*"
}

