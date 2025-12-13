# EventBridge Rule for Monthly Expense Checks
# Runs on the 1st of each month at 9 AM UTC

resource "aws_cloudwatch_event_rule" "monthly_expense_check" {
  name                = "${var.project_name}-${var.environment}-monthly-expense-check"
  description         = "Trigger monthly expense threshold check"
  schedule_expression = "cron(0 9 1 * ? *)"  # 9 AM UTC on the 1st of each month

  tags = {
    Name = "${var.project_name}-${var.environment}-monthly-check"
  }
}

resource "aws_cloudwatch_event_target" "expense_notifier" {
  rule      = aws_cloudwatch_event_rule.monthly_expense_check.name
  target_id = "ExpenseNotifierTarget"
  arn       = aws_lambda_function.expense_notifier.arn
}

# Lambda Permission for EventBridge
resource "aws_lambda_permission" "eventbridge_invoke" {
  statement_id  = "AllowExecutionFromEventBridge"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.expense_notifier.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.monthly_expense_check.arn
}

