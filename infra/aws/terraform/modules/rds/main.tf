# Amazon RDS PostgreSQL 16 Module — ap-south-1

resource "aws_db_subnet_group" "rds" {
  name        = "fashx-${var.environment}-db-subnet-group"
  subnet_ids  = var.subnet_ids
  description = "Private DB subnet group for FashX ${var.environment}"

  tags = {
    Name        = "fashx-${var.environment}-db-subnet-group"
    Environment = var.environment
  }
}

resource "aws_security_group" "rds" {
  name        = "fashx-${var.environment}-rds-sg"
  description = "Controls ingress traffic to RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from ECS application tasks"
    from_port       = 5432
    to_port         = 5432
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
    Name        = "fashx-${var.environment}-rds-sg"
    Environment = var.environment
  }
}

# Parameter group supporting pgvector
resource "aws_db_parameter_group" "pg16" {
  name        = "fashx-${var.environment}-pg16-params"
  family      = "postgres16"
  description = "PostgreSQL 16 parameter group with pgvector for ${var.environment}"

  parameter {
    name  = "rds.force_ssl"
    value = "1"
  }

  parameter {
    name  = "shared_preload_libraries"
    value = "vector"
  }

  tags = {
    Environment = var.environment
  }
}

resource "random_password" "db_master" {
  length           = 32
  special          = true
  override_special = "!#$%&*()-_=+[]{}<>:?"
}

resource "aws_db_instance" "postgres" {
  identifier                  = "fashx-pg-${var.environment}"
  engine                      = "postgres"
  engine_version              = "16.2"
  instance_class              = var.instance_class
  allocated_storage           = var.allocated_storage
  max_allocated_storage       = var.allocated_storage * 5
  storage_type                = "gp3"
  storage_encrypted           = true
  db_name                     = var.database_name
  username                    = "fashx_app"
  password                    = random_password.db_master.result
  db_subnet_group_name        = aws_db_subnet_group.rds.name
  vpc_security_group_ids      = [aws_security_group.rds.id]
  parameter_group_name        = aws_db_parameter_group.pg16.name
  publicly_accessible         = false
  multi_az                    = var.multi_az
  backup_retention_period     = var.backup_retention_days
  backup_window               = "19:00-20:00" # 00:30-01:30 IST
  maintenance_window          = "sun:20:00-sun:21:00"
  auto_minor_version_upgrade  = true
  deletion_protection         = var.environment == "prod" ? true : false
  skip_final_snapshot         = var.environment == "prod" ? false : true
  final_snapshot_identifier   = "fashx-pg-${var.environment}-final-snapshot"
  copy_tags_to_snapshot       = true

  tags = {
    Name        = "fashx-pg-${var.environment}"
    Environment = var.environment
  }
}
