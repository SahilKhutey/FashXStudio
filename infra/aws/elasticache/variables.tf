variable "aws_region" {
  description = "AWS region for ElastiCache Redis resources."
  type        = string
  default     = "ap-south-1"
}

variable "vpc_id" {
  description = "VPC ID where the cache subnet group and security groups reside."
  type        = string
}

variable "cache_subnet_ids" {
  description = "List of private subnet IDs for ElastiCache subnet group (at least 2 subnets across distinct AZs)."
  type        = list(string)
  validation {
    condition     = length(var.cache_subnet_ids) >= 2
    error_message = "At least two private subnets in distinct AZs are required for ElastiCache multi-AZ topology."
  }
}

variable "app_security_group_ids" {
  description = "Security group IDs of application servers and workers authorized to access Redis on port 6379."
  type        = list(string)
  validation {
    condition     = length(var.app_security_group_ids) >= 1
    error_message = "At least one application security group must be provided."
  }
}

variable "engine_version" {
  description = "Redis engine version (7.1 recommended for ElastiCache in ap-south-1)."
  type        = string
  default     = "7.1"
}

variable "port" {
  description = "TCP port for Redis cluster."
  type        = number
  default     = 6379
}

variable "dev_node_type" {
  description = "ElastiCache node instance class for development environment."
  type        = string
  default     = "cache.t4g.micro"
}

variable "staging_node_type" {
  description = "ElastiCache node instance class for staging environment."
  type        = string
  default     = "cache.t4g.small"
}

variable "prod_node_type" {
  description = "ElastiCache node instance class for production environment."
  type        = string
  default     = "cache.r6g.large"
}

variable "kms_key_arn" {
  description = "Optional customer-managed KMS key ARN for production at-rest encryption. If null, AWS-managed key is used."
  type        = string
  default     = null
}

variable "snapshot_window" {
  description = "Daily time range (in UTC) during which automated snapshots are created for production."
  type        = string
  default     = "02:00-03:00"
}

variable "maintenance_window" {
  description = "Weekly time range (in UTC) during which maintenance can occur."
  type        = string
  default     = "sun:03:30-sun:04:30"
}
