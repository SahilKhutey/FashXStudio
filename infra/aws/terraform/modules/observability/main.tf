# CloudWatch Observability & SNS Alerting Module — ap-south-1

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/fashx/${var.environment}"
  retention_in_days = var.environment == "prod" ? 30 : (var.environment == "staging" ? 14 : 7)

  tags = {
    Environment = var.environment
  }
}

resource "aws_sns_topic" "alerts" {
  name = "fashx-alerts-${var.environment}"

  tags = {
    Environment = var.environment
  }
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alarm_email
}

# P1 Critical Alarm: API 5xx Surge
resource "aws_cloudwatch_metric_alarm" "api_5xx" {
  alarm_name          = "API-5xx-Rate-High-${var.environment}"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "Api5xxErrors"
  namespace           = "FashX/API"
  period              = 60
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Triggers when API returns > 10 5xx server errors within 2 minutes."
  alarm_actions       = [aws_sns_topic.alerts.arn]

  dimensions = {
    Environment = var.environment
  }
}
