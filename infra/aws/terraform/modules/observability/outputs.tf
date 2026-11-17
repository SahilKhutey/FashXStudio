output "log_group_name" {
  value       = aws_cloudwatch_log_group.ecs.name
  description = "Name of the CloudWatch log group"
}

output "log_group_arn" {
  value       = aws_cloudwatch_log_group.ecs.arn
  description = "ARN of the CloudWatch log group"
}

output "sns_alerts_topic_arn" {
  value       = aws_sns_topic.alerts.arn
  description = "ARN of the SNS operational alerts topic"
}
