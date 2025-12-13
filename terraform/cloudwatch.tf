# CloudWatch Metrics and Alarms Configuration

# ============================================
# CloudWatch Alarms
# ============================================

# Alarm: ProcessReceipt Lambda errors > 5 in 1 minute
resource "aws_cloudwatch_metric_alarm" "lambda_errors" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-errors"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Errors"
  namespace           = "AWS/Lambda"
  period              = 60  # 1 minute
  statistic           = "Sum"
  threshold           = 5
  alarm_description   = "Alert when ProcessReceipt Lambda errors exceed 5 in 1 minute"
  treat_missing_data = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.receipt_processor.function_name
  }

  alarm_actions = []  # Can add SNS topic here for notifications

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-errors-alarm"
  }
}

# Alarm: Lambda duration (if processing takes too long)
resource "aws_cloudwatch_metric_alarm" "lambda_duration" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-duration"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Duration"
  namespace           = "AWS/Lambda"
  period              = 300  # 5 minutes
  statistic           = "Average"
  threshold           = 25000  # 25 seconds (close to 30s timeout)
  alarm_description   = "Alert when Lambda execution duration is high"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.receipt_processor.function_name
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-duration-alarm"
  }
}

# Alarm: Lambda throttles
resource "aws_cloudwatch_metric_alarm" "lambda_throttles" {
  alarm_name          = "${var.project_name}-${var.environment}-lambda-throttles"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "Throttles"
  namespace           = "AWS/Lambda"
  period              = 300  # 5 minutes
  statistic           = "Sum"
  threshold           = 1
  alarm_description   = "Alert when Lambda function is throttled"
  treat_missing_data  = "notBreaching"

  dimensions = {
    FunctionName = aws_lambda_function.receipt_processor.function_name
  }

  tags = {
    Name = "${var.project_name}-${var.environment}-lambda-throttles-alarm"
  }
}

# ============================================
# Custom CloudWatch Metrics Alarms
# ============================================
# Note: Custom metrics are published from Lambda functions
# These alarms monitor the custom metrics

# Alarm: Threshold exceeded count (tracks how many users exceeded threshold)
resource "aws_cloudwatch_metric_alarm" "threshold_exceeded" {
  alarm_name          = "${var.project_name}-${var.environment}-threshold-exceeded"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "ThresholdExceeded"
  namespace           = "SmartExpenseMonitor"
  period              = 3600  # 1 hour
  statistic           = "Sum"
  threshold           = 0
  alarm_description   = "Alert when any user exceeds their monthly spending threshold"
  treat_missing_data  = "notBreaching"

  tags = {
    Name = "${var.project_name}-${var.environment}-threshold-exceeded-alarm"
  }
}

# ============================================
# CloudWatch Dashboard (Optional)
# ============================================

resource "aws_cloudwatch_dashboard" "expense_monitor" {
  dashboard_name = "${var.project_name}-${var.environment}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type   = "metric"
        x      = 0
        y      = 0
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/Lambda", "Invocations", { "stat" = "Sum", "label" = "Receipt Processor Invocations" }],
            ["AWS/Lambda", "Errors", { "stat" = "Sum", "label" = "Errors" }],
            ["AWS/Lambda", "Duration", { "stat" = "Average", "label" = "Avg Duration (ms)" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Lambda Function Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 6
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["AWS/DynamoDB", "ConsumedReadCapacityUnits", { "stat" = "Sum", "label" = "DynamoDB Reads" }],
            ["AWS/DynamoDB", "ConsumedWriteCapacityUnits", { "stat" = "Sum", "label" = "DynamoDB Writes" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "DynamoDB Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 12
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["SmartExpenseMonitor", "ExpensesProcessed", { "stat" = "Sum", "label" = "Expenses Processed" }],
            ["SmartExpenseMonitor", "TotalExpenseAmount", { "stat" = "Sum", "label" = "Total Expense Amount" }],
            ["SmartExpenseMonitor", "TextractProcessingTime", { "stat" = "Average", "label" = "Avg Textract Time (ms)" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Custom Application Metrics"
          period  = 300
        }
      },
      {
        type   = "metric"
        x      = 0
        y      = 18
        width  = 12
        height = 6

        properties = {
          metrics = [
            ["SmartExpenseMonitor", "MonthlySpending", { "stat" = "Sum", "label" = "Monthly Spending" }],
            ["SmartExpenseMonitor", "ThresholdExceeded", { "stat" = "Sum", "label" = "Threshold Exceeded Count" }]
          ]
          view    = "timeSeries"
          stacked = false
          region  = var.aws_region
          title   = "Monthly Spending Metrics"
          period  = 3600
        }
      }
    ]
  })
}

