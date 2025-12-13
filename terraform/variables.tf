variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "smart-expense-monitor"
}

variable "cognito_user_pool_name" {
  description = "Name for Cognito User Pool"
  type        = string
  default     = "expense-monitor-users"
}

variable "s3_bucket_name" {
  description = "Name for S3 bucket (must be globally unique)"
  type        = string
  default     = ""
}

variable "lambda_runtime" {
  description = "Lambda runtime for functions"
  type        = string
  default     = "python3.11"
}

variable "lambda_timeout" {
  description = "Lambda function timeout in seconds"
  type        = number
  default     = 30
}

variable "lambda_memory_size" {
  description = "Lambda function memory size in MB"
  type        = number
  default     = 256
}

variable "enable_textract" {
  description = "Enable AWS Textract for OCR processing"
  type        = bool
  default     = true
}

variable "allowed_origins" {
  description = "Allowed CORS origins for API Gateway"
  type        = list(string)
  default     = ["*"]
}

variable "cognito_callback_urls" {
  description = "Cognito callback URLs (must include scheme: http:// or https://)"
  type        = list(string)
  default     = ["http://localhost:3000", "http://localhost:3000/callback"]
}

variable "ses_sender_email" {
  description = "SES sender email address (must be verified in SES)"
  type        = string
  default     = "shraym@proton.me"
}

