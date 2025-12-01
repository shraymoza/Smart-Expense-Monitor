provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "Smart-Expense-Monitor"
      Environment = var.environment
      ManagedBy   = "Terraform"
    }
  }
}

