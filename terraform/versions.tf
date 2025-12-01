terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.0"
    }
  }

  # Uncomment and configure if using remote state
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "smart-expense-monitor/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

