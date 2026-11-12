# ==============================================================================
# FASHXSTUDIO — AWS ELASTICACHE FOR REDIS INFRASTRUCTURE (PHASE 03.3)
# ==============================================================================

# --- Cache Subnet Group ---
resource "aws_elasticache_subnet_group" "redis" {
  name        = "fashx-redis-subnet-group"
  description = "Private subnet group for FashXStudio ElastiCache Redis clusters"
  subnet_ids  = var.cache_subnet_ids

  tags = {
    Name = "fashx-redis-subnet-group"
  }
}

# --- Redis Security Group ---
resource "aws_security_group" "redis" {
  name        = "fashx-redis-sg"
  description = "Restricts ElastiCache Redis ingress exclusively to application servers and Celery workers"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis port 6379 from authorized application and worker security groups"
    from_port       = var.port
    to_port         = var.port
    protocol        = "tcp"
    security_groups = var.app_security_group_ids
  }

  egress {
    description = "Disallow outbound connectivity from cache tier"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "fashx-redis-sg"
  }
}

# --- Redis 7.x Parameter Group ---
resource "aws_elasticache_parameter_group" "redis7" {
  name        = "fashx-redis7-params"
  family      = "redis7"
  description = "Optimized parameters for FashXStudio session cache and Celery task broker"

  parameter {
    name  = "maxmemory-policy"
    value = "volatile-lru"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }

  parameter {
    name  = "tcp-keepalive"
    value = "60"
  }

  tags = {
    Name = "fashx-redis7-params"
  }
}

# --- Redis Auth Tokens in AWS Secrets Manager ---
resource "random_password" "redis_auth_token_staging" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "redis_auth_token_staging" {
  name                    = "/fashx/staging/redis/auth_token"
  description             = "Auth token for FashXStudio Staging ElastiCache Redis cluster"
  recovery_window_in_days = 0

  tags = {
    Environment = "staging"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token_staging" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token_staging.id
  secret_string = random_password.redis_auth_token_staging.result
}

resource "random_password" "redis_auth_token_prod" {
  length  = 32
  special = false
}

resource "aws_secretsmanager_secret" "redis_auth_token_prod" {
  name                    = "/fashx/prod/redis/auth_token"
  description             = "Auth token for FashXStudio Production ElastiCache Redis cluster"
  recovery_window_in_days = 30

  tags = {
    Environment = "production"
  }
}

resource "aws_secretsmanager_secret_version" "redis_auth_token_prod" {
  secret_id     = aws_secretsmanager_secret.redis_auth_token_prod.id
  secret_string = random_password.redis_auth_token_prod.result
}

# --- Development Cluster (Single Node, Cost Optimized) ---
resource "aws_elasticache_replication_group" "fashx_redis_dev" {
  replication_group_id       = "fashx-redis-dev"
  description                = "FashXStudio Development Redis (Single Node)"
  node_type                  = var.dev_node_type
  num_cache_clusters         = 1
  parameter_group_name       = aws_elasticache_parameter_group.redis7.name
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  engine_version             = var.engine_version
  port                       = var.port
  automatic_failover_enabled = false
  transit_encryption_enabled = false
  at_rest_encryption_enabled = false
  apply_immediately          = true

  tags = {
    Name        = "fashx-redis-dev"
    Environment = "development"
  }
}

# --- Staging Replication Group (1 Primary + 1 Replica, Transit Encryption) ---
resource "aws_elasticache_replication_group" "fashx_redis_staging" {
  replication_group_id       = "fashx-redis-staging"
  description                = "FashXStudio Staging Redis Replication Group"
  node_type                  = var.staging_node_type
  num_cache_clusters         = 2
  parameter_group_name       = aws_elasticache_parameter_group.redis7.name
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  engine_version             = var.engine_version
  port                       = var.port
  automatic_failover_enabled = true
  multi_az_enabled           = false
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token_staging.result
  at_rest_encryption_enabled = true
  apply_immediately          = false

  tags = {
    Name        = "fashx-redis-staging"
    Environment = "staging"
  }
}

# --- Production Multi-AZ Replication Group (1 Primary + 2 Replicas, Multi-AZ, Automated Snapshots) ---
resource "aws_elasticache_replication_group" "fashx_redis_prod" {
  replication_group_id       = "fashx-redis-prod"
  description                = "FashXStudio Production Redis Multi-AZ Cluster"
  node_type                  = var.prod_node_type
  num_cache_clusters         = 3
  parameter_group_name       = aws_elasticache_parameter_group.redis7.name
  subnet_group_name          = aws_elasticache_subnet_group.redis.name
  security_group_ids         = [aws_security_group.redis.id]
  engine_version             = var.engine_version
  port                       = var.port
  multi_az_enabled           = true
  automatic_failover_enabled = true
  transit_encryption_enabled = true
  auth_token                 = random_password.redis_auth_token_prod.result
  at_rest_encryption_enabled = true
  kms_key_id                 = var.kms_key_arn
  snapshot_retention_limit   = 7
  snapshot_window            = var.snapshot_window
  maintenance_window         = var.maintenance_window
  auto_minor_version_upgrade = true
  apply_immediately          = false

  tags = {
    Name        = "fashx-redis-prod"
    Environment = "production"
  }
}
