variable "aws_region" {
  description = "AWS region for FashX databases."
  type        = string
  default     = "ap-south-1"
}

variable "vpc_id" {
  description = "Existing FashX VPC ID."
  type        = string
}

variable "private_subnet_ids" {
  description = "At least two private subnets in different AZs."
  type        = list(string)

  validation {
    condition     = length(var.private_subnet_ids) >= 2
    error_message = "Provide at least two private subnets in different Availability Zones."
  }
}

variable "app_security_group_ids" {
  description = "Existing application security group per environment."
  type = object({
    dev     = string
    staging = string
    prod    = string
  })
}

variable "postgres_engine_version" {
  description = "Exact PostgreSQL 16 minor version available in ap-south-1."
  type        = string
  default     = "16.3"
}

variable "master_username" {
  description = "RDS administrative account; never use it in the app."
  type        = string
  default     = "fashx_admin"
}

variable "allocated_storage_gb" {
  description = "Initial allocated storage in GB."
  type        = number
  default     = 20
}

variable "max_allocated_storage_gb" {
  description = "Maximum storage autoscaling ceiling in GB."
  type        = number
  default     = 100
}

variable "instance_classes" {
  description = "Initial database instance classes; tune after benchmarks."
  type = object({
    dev     = string
    staging = string
    prod    = string
  })

  default = {
    dev     = "db.t4g.micro"
    staging = "db.t4g.small"
    prod    = "db.t4g.medium"
  }
}

variable "rds_kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for RDS storage encryption."
  type        = string
  default     = null
}
