# Staging Environment Root Module — AWS ap-south-1 (Mumbai)

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "FashXStudio"
      Environment = var.environment
      ManagedBy   = "terraform"
    }
  }
}

module "networking" {
  source      = "../../modules/networking"
  environment = var.environment
}

module "s3" {
  source      = "../../modules/s3"
  environment = var.environment
  account_id  = var.account_id
}

module "ecs" {
  source                 = "../../modules/ecs"
  environment            = var.environment
  vpc_id                 = module.networking.vpc_id
  public_subnet_ids      = module.networking.public_subnet_ids
  private_app_subnet_ids = module.networking.private_app_subnet_ids
  s3_bucket_arn          = module.s3.bucket_arn
}

module "rds" {
  source                = "../../modules/rds"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  subnet_ids            = module.networking.private_data_subnet_ids
  app_security_group_id = module.ecs.ecs_tasks_security_group_id
  instance_class        = "db.t4g.small"
  allocated_storage     = 20
  backup_retention_days = 14
  multi_az              = false
  database_name         = "fashx_staging"
}

module "elasticache" {
  source                = "../../modules/elasticache"
  environment           = var.environment
  vpc_id                = module.networking.vpc_id
  subnet_ids            = module.networking.private_data_subnet_ids
  app_security_group_id = module.ecs.ecs_tasks_security_group_id
  node_type             = "cache.t4g.micro"
}

module "secrets" {
  source       = "../../modules/secrets"
  environment  = var.environment
  database_url = "postgresql+asyncpg://fashx_app:${module.rds.db_master_password}@${module.rds.db_endpoint}/${module.rds.db_name}"
  redis_url    = "rediss://:${module.elasticache.auth_token}@${module.elasticache.primary_endpoint_address}:${module.elasticache.port}/0"
}

module "observability" {
  source      = "../../modules/observability"
  environment = var.environment
}

module "cognito" {
  source         = "../../modules/cognito"
  environment    = var.environment
  aws_account_id = var.account_id
  callback_urls  = ["fashx-staging://auth/callback", "fashx://auth/callback"]
  logout_urls    = ["fashx-staging://auth/logout", "fashx://auth/logout"]
}
