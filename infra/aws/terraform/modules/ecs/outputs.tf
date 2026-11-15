output "cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "Name of the ECS cluster"
}

output "cluster_id" {
  value       = aws_ecs_cluster.main.id
  description = "ID of the ECS cluster"
}

output "ecs_tasks_security_group_id" {
  value       = aws_security_group.ecs_tasks.id
  description = "Security group ID for ECS tasks"
}

output "alb_dns_name" {
  value       = aws_lb.api.dns_name
  description = "DNS name of the Application Load Balancer"
}

output "alb_target_group_arn" {
  value       = aws_lb_target_group.api.arn
  description = "ARN of the ALB target group"
}

output "execution_role_arn" {
  value       = aws_iam_role.ecs_execution.arn
  description = "ARN of the ECS execution role"
}

output "task_role_arn" {
  value       = aws_iam_role.ecs_task.arn
  description = "ARN of the ECS task role"
}
