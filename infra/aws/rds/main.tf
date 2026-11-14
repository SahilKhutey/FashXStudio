locals {
  environments = {
    dev = {
      identifier     = "fashx-pg-dev"
      database_name  = "fashx_dev"
      backup_days    = 7
      multi_az       = false
      final_snapshot = "fashx-pg-dev-final"
    }

    staging = {
      identifier     = "fashx-pg-staging"
      database_name  = "fashx_staging"
      backup_days    = 14
      multi_az       = false
      final_snapshot = "fashx-pg-staging-final"
    }

    prod = {
      identifier     = "fashx-pg-prod"
      database_name  = "fashx_prod"
      backup_days    = 30
      multi_az       = true
      final_snapshot = "fashx-pg-prod-final"
    }
  }

  environment_app_security_groups = {
    dev     = var.app_security_group_ids.dev
    staging = var.app_security_group_ids.staging
    prod    = var.app_security_group_ids.prod
  }
}

resource "aws_db_subnet_group" "fashx" {
  name       = "fashx-private-db-subnets"
  subnet_ids = var.private_subnet_ids

  description = "Private subnets for FashX PostgreSQL instances"

  tags = {
    Name = "fashx-private-db-subnets"
  }
}

resource "aws_db_parameter_group" "postgres16" {
  name        = "fashx-postgres16"
  family      = "postgres16"
  description = "FashX PostgreSQL 16 security and performance parameters"

  parameter {
    name         = "rds.force_ssl"
    value        = "1"
    apply_method = "pending-reboot"
  }

  tags = {
    Name = "fashx-postgres16"
  }
}

resource "aws_security_group" "database" {
  for_each = local.environments

  name        = "fashx-${each.key}-postgres"
  description = "PostgreSQL access only from FashX ${each.key} application"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from matching environment application"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [
      local.environment_app_security_groups[each.key]
    ]
  }

  # No database-initiated outbound traffic is required for ordinary application connectivity.
  egress = []

  tags = {
    Name        = "fashx-${each.key}-postgres"
    Environment = each.key
  }
}

resource "aws_db_instance" "database" {
  for_each = local.environments

  identifier = each.value.identifier

  engine         = "postgres"
  engine_version = var.postgres_engine_version
  instance_class = var.instance_classes[each.key]

  db_name  = each.value.database_name
  username = var.master_username

  # AWS creates and manages the master password in Secrets Manager.
  manage_master_user_password = true

  allocated_storage     = var.allocated_storage_gb
  max_allocated_storage = var.max_allocated_storage_gb
  storage_type          = "gp3"
  storage_encrypted     = true
  kms_key_id            = var.rds_kms_key_arn

  port                   = 5432
  publicly_accessible    = false
  multi_az               = each.value.multi_az
  db_subnet_group_name   = aws_db_subnet_group.fashx.name
  vpc_security_group_ids = [
    aws_security_group.database[each.key].id
  ]

  parameter_group_name = aws_db_parameter_group.postgres16.name

  backup_retention_period = each.value.backup_days
  backup_window           = "18:00-18:30"
  maintenance_window      = "sun:19:00-sun:20:00"
  copy_tags_to_snapshot   = true

  auto_minor_version_upgrade  = true
  allow_major_version_upgrade = false
  apply_immediately           = false

  enabled_cloudwatch_logs_exports = [
    "postgresql",
    "upgrade"
  ]

  monitoring_interval = 0

  deletion_protection       = true
  skip_final_snapshot       = false
  final_snapshot_identifier = each.value.final_snapshot

  iam_database_authentication_enabled = false

  tags = {
    Name        = each.value.identifier
    Environment = each.key
    Database    = each.value.database_name
  }

  lifecycle {
    prevent_destroy = true
  }
}
