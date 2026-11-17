output "primary_endpoint_address" {
  value       = aws_elasticache_replication_group.valkey.primary_endpoint_address
  description = "Address of the primary endpoint for the replication group"
}

output "port" {
  value       = aws_elasticache_replication_group.valkey.port
  description = "Port number on which the cache accepts connections"
}

output "auth_token" {
  value       = random_password.redis_auth.result
  sensitive   = true
  description = "Redis transit encryption auth token"
}

output "security_group_id" {
  value       = aws_security_group.cache.id
  description = "Security group ID of the ElastiCache cluster"
}
