output "db_instance_id" {
  value       = aws_db_instance.postgres.id
  description = "The RDS instance identifier"
}

output "db_endpoint" {
  value       = aws_db_instance.postgres.endpoint
  description = "The connection endpoint for PostgreSQL"
}

output "db_address" {
  value       = aws_db_instance.postgres.address
  description = "The hostname of the database instance"
}

output "db_port" {
  value       = aws_db_instance.postgres.port
  description = "The port PostgreSQL listens on"
}

output "db_name" {
  value       = aws_db_instance.postgres.db_name
  description = "The database name"
}

output "db_security_group_id" {
  value       = aws_security_group.rds.id
  description = "Security group ID of the RDS instance"
}

output "db_master_password" {
  value       = random_password.db_master.result
  sensitive   = true
  description = "Generated master database password"
}
