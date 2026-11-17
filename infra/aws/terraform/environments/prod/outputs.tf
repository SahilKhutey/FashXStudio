output "alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "Public DNS of the Production ALB"
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "Production ECS Cluster Name"
}

output "rds_endpoint" {
  value       = module.rds.db_endpoint
  description = "Production PostgreSQL Endpoint"
}

output "elasticache_endpoint" {
  value       = module.elasticache.primary_endpoint_address
  description = "Production Valkey/Redis Endpoint"
}

output "s3_bucket" {
  value       = module.s3.bucket_name
  description = "Production S3 Bucket"
}

output "cognito_user_pool_id" {
  value       = module.cognito.user_pool_id
  description = "Production Cognito User Pool ID"
}

output "cognito_client_id" {
  value       = module.cognito.user_pool_client_id
  description = "Production Cognito Public Client ID"
}

output "cognito_jwks_url" {
  value       = module.cognito.jwks_url
  description = "Production Cognito Public JWKS URL"
}
