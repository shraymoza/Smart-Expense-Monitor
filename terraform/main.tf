# Main Terraform configuration file
# This file can be used for any additional resources or configurations

# Data source for current AWS region
data "aws_region" "current" {}

# Data source for current AWS account
data "aws_caller_identity" "current" {}

