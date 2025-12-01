# S3 Bucket for storing receipts
resource "aws_s3_bucket" "receipts" {
  bucket = var.s3_bucket_name != "" ? var.s3_bucket_name : "${var.project_name}-${var.environment}-receipts-${random_id.bucket_suffix.hex}"

  tags = {
    Name = "${var.project_name}-${var.environment}-receipts"
  }
}

# Random ID for bucket name uniqueness
resource "random_id" "bucket_suffix" {
  byte_length = 4
}

# S3 Bucket Versioning
resource "aws_s3_bucket_versioning" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket Server Side Encryption
resource "aws_s3_bucket_server_side_encryption_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# S3 Bucket Public Access Block
resource "aws_s3_bucket_public_access_block" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# S3 Bucket CORS Configuration
# Required for frontend to upload files directly to S3 using presigned URLs
resource "aws_s3_bucket_cors_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  cors_rule {
    allowed_headers = ["*"]
    allowed_methods = ["GET", "PUT", "POST", "HEAD"]
    allowed_origins = ["*"]  # In production, replace with your frontend domain
    expose_headers  = ["ETag"]
    max_age_seconds = 3000
  }
}

# S3 Bucket Lifecycle Configuration
resource "aws_s3_bucket_lifecycle_configuration" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  rule {
    id     = "delete_old_receipts"
    status = "Enabled"

    filter {}

    expiration {
      days = 365 # Keep receipts for 1 year
    }
  }
}

# S3 Bucket Notification for Lambda trigger
# Triggers on uploads to any user's folder: users/{userId}/uploads/
resource "aws_s3_bucket_notification" "receipts" {
  bucket = aws_s3_bucket.receipts.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.receipt_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "users/"
    filter_suffix       = ".jpg"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.receipt_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "users/"
    filter_suffix       = ".jpeg"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.receipt_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "users/"
    filter_suffix       = ".png"
  }

  lambda_function {
    lambda_function_arn = aws_lambda_function.receipt_processor.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "users/"
    filter_suffix       = ".pdf"
  }

  depends_on = [aws_lambda_permission.s3_invoke]
}

# Note: User-specific access is enforced through:
# 1. API Gateway with Cognito authorizer (ensures authenticated requests)
# 2. Lambda function extracts userId from S3 key path
# 3. DynamoDB queries filter by userId
# 4. Frontend uploads to users/{userId}/uploads/ path
# 
# Direct S3 access is blocked (bucket is private)
# All access goes through API Gateway + Lambda which enforces user isolation

