# Amazon ElastiCache for Valkey / Redis 7.2 Module — ap-south-1

resource "aws_elasticache_subnet_group" "cache" {
  name        = "fashx-${var.environment}-cache-subnet-group"
  subnet_ids  = var.subnet_ids
  description = "Private cache subnet group for FashX ${var.environment}"
}

resource "aws_security_group" "cache" {
  name        = "fashx-${var.environment}-cache-sg"
  description = "Controls ingress traffic to ElastiCache Valkey/Redis"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Redis protocol from ECS tasks"
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [var.app_security_group_id]
  }

  egress {
    from_port        = 0
    to_port          = 0
    protocol         = "-1"
    cidr_blocks      = ["0.0.0.0/0"]
    ipv6_cidr_blocks = ["::/0"]
  }

  tags = {
    Name        = "fashx-${var.environment}-cache-sg"
    Environment = var.environment
  }
}

# Parameter group enforcing noeviction for durable task queues
resource "aws_elasticache_parameter_group" "redis7" {
  name        = "fashx-${var.environment}-valkey7-params"
  family      = "redis7"
  description = "Redis 7.2 / Valkey parameter group for Celery broker"

  parameter {
    name  = "maxmemory-policy"
    value = "noeviction"
  }

  parameter {
    name  = "timeout"
    value = "300"
  }
}

resource "random_password" "redis_auth" {
  length  = 32
  special = false
}

resource "aws_elasticache_replication_group" "valkey" {
  replication_group_id       = "fashx-${var.environment}-valkey"
  description                = "Celery task queue broker for FashX ${var.environment}"
  engine                     = "redis"
  engine_version             = "7.1"
  node_type                  = var.node_type
  num_cache_clusters         = 1
  port                       = 6379
  parameter_group_name       = aws_elasticache_parameter_group.redis7.name
  subnet_group_name          = aws_elasticache_subnet_group.cache.name
  security_group_ids         = [aws_security_group.cache.id]
  transit_encryption_enabled = true
  at_rest_encryption_enabled = true
  auth_token                 = random_password.redis_auth.result
  auto_minor_version_upgrade = true

  tags = {
    Name        = "fashx-${var.environment}-valkey"
    Environment = var.environment
  }
}
