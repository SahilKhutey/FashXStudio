output "alb_dns_name" {
  value       = module.ecs.alb_dns_name
  description = "Public DNS of the Staging ALB"
}

output "ecs_cluster_name" {
  value       = module.ecs.cluster_name
  description = "Staging ECS Cluster Name"
}

output "rds_endpoint" {
  value       = module.rds.db_endpoint
  description = "Staging PostgreSQL Endpoint"
}

output "elasticache_endpoint" {
  value       = module.elasticache.primary_endpoint_address
  description = "Staging Valkey/Redis Endpoint"
}

output "s3_bucket" {
  value       = module.s3.bucket_name
  description = "Staging S3 Bucket"
}
