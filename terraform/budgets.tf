# AWS Budgets Configuration
# Monitors forecasted monthly spend and sends alerts

resource "aws_budgets_budget" "monthly_budget" {
  name              = "${var.project_name}-${var.environment}-monthly-budget"
  budget_type       = "COST"
  limit_amount      = "15"
  limit_unit        = "USD"
  time_period_start = "2024-01-01_00:00"
  time_unit         = "MONTHLY"

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 80  # Alert at 80% of budget ($12)
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.ses_sender_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100  # Alert at 100% of budget ($15)
    threshold_type             = "PERCENTAGE"
    notification_type          = "ACTUAL"
    subscriber_email_addresses = [var.ses_sender_email]
  }

  notification {
    comparison_operator        = "GREATER_THAN"
    threshold                  = 100  # Alert if forecasted to exceed
    threshold_type             = "PERCENTAGE"
    notification_type          = "FORECASTED"
    subscriber_email_addresses = [var.ses_sender_email]
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-budget"
  }
}

