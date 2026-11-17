variable "environment" {
  type        = string
  description = "Deployment environment name (dev, staging, prod)"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where RDS is provisioned"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private data subnet IDs for the DB subnet group"
}

variable "app_security_group_id" {
  type        = string
  description = "Security group ID of the ECS application tasks allowed to connect"
}

variable "instance_class" {
  type        = string
  description = "RDS instance compute class"
  default     = "db.t4g.small"
}

variable "allocated_storage" {
  type        = number
  description = "Allocated storage in GB"
  default     = 20
}

variable "backup_retention_days" {
  type        = number
  description = "Number of days to retain automated backups"
  default     = 14
}

variable "multi_az" {
  type        = bool
  description = "Whether to provision Multi-AZ standby replica"
  default     = false
}

variable "database_name" {
  type        = string
  description = "Name of the initial PostgreSQL database"
}
