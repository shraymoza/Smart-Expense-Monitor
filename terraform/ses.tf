# SES Configuration for Email Notifications
# Note: SES requires email verification in sandbox mode
# For production, request production access from AWS

# SES Email Identity (sender email)
resource "aws_ses_email_identity" "sender" {
  email = var.ses_sender_email
}

# SES Configuration Set (optional, for tracking)
resource "aws_ses_configuration_set" "notifications" {
  name = "${var.project_name}-${var.environment}-notifications"
}

# SES Event Destination for tracking (optional)
resource "aws_ses_event_destination" "cloudwatch" {
  name                   = "cloudwatch-destination"
  configuration_set_name = aws_ses_configuration_set.notifications.name
  enabled                = true
  matching_types         = ["send", "reject", "bounce", "complaint", "delivery", "open", "click"]

  cloudwatch_destination {
    default_value  = "default"
    dimension_name = "MessageTag"
    value_source   = "messageTag"
  }
}

