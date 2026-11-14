output "redis_security_group_id" {
  description = "Security Group ID guarding ElastiCache Redis cluster ingress"
  value       = aws_security_group.redis.id
}

output "dev_primary_endpoint" {
  description = "Primary endpoint address for development Redis instance"
  value       = aws_elasticache_replication_group.fashx_redis_dev.primary_endpoint_address
}

output "staging_primary_endpoint" {
  description = "Primary write endpoint address for staging Redis replication group"
  value       = aws_elasticache_replication_group.fashx_redis_staging.primary_endpoint_address
}

output "staging_reader_endpoint" {
  description = "Read-only endpoint address for staging Redis replication group"
  value       = aws_elasticache_replication_group.fashx_redis_staging.reader_endpoint_address
}

output "prod_primary_endpoint" {
  description = "Primary write endpoint address for production Redis Multi-AZ cluster"
  value       = aws_elasticache_replication_group.fashx_redis_prod.primary_endpoint_address
}

output "prod_reader_endpoint" {
  description = "Read-only endpoint address for production Redis Multi-AZ cluster"
  value       = aws_elasticache_replication_group.fashx_redis_prod.reader_endpoint_address
}

output "staging_auth_token_secret_arn" {
  description = "AWS Secrets Manager ARN for Staging Redis AUTH token"
  value       = aws_secretsmanager_secret.redis_auth_token_staging.arn
}

output "prod_auth_token_secret_arn" {
  description = "AWS Secrets Manager ARN for Production Redis AUTH token"
  value       = aws_secretsmanager_secret.redis_auth_token_prod.arn
}
