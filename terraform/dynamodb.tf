# DynamoDB Table for Expenses
resource "aws_dynamodb_table" "expenses" {
  name           = "${var.project_name}-${var.environment}-expenses"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "userId"
  range_key      = "expenseId"

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "expenseId"
    type = "S"
  }

  # Global Secondary Index for querying by date
  global_secondary_index {
    name            = "DateIndex"
    hash_key        = "userId"
    range_key       = "date"
    projection_type = "ALL"
  }

  attribute {
    name = "date"
    type = "S"
  }

  # Global Secondary Index for querying by store
  global_secondary_index {
    name            = "StoreIndex"
    hash_key        = "userId"
    range_key       = "storeName"
    projection_type = "ALL"
  }

  attribute {
    name = "storeName"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-expenses"
  }
}

# DynamoDB Table for Receipt Metadata
resource "aws_dynamodb_table" "receipts" {
  name           = "${var.project_name}-${var.environment}-receipts"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "receiptId"

  attribute {
    name = "receiptId"
    type = "S"
  }

  # Global Secondary Index for querying by user
  global_secondary_index {
    name            = "UserIndex"
    hash_key        = "userId"
    range_key       = "uploadDate"
    projection_type = "ALL"
  }

  attribute {
    name = "userId"
    type = "S"
  }

  attribute {
    name = "uploadDate"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-receipts"
  }
}

# DynamoDB Table for User Settings
resource "aws_dynamodb_table" "user_settings" {
  name         = "${var.project_name}-${var.environment}-user-settings"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "userId"

  attribute {
    name = "userId"
    type = "S"
  }

  point_in_time_recovery {
    enabled = true
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-user-settings"
  }
}

