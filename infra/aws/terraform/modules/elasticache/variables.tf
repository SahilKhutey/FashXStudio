variable "environment" {
  type        = string
  description = "Deployment environment name (dev, staging, prod)"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where ElastiCache is provisioned"
}

variable "subnet_ids" {
  type        = list(string)
  description = "Private data subnet IDs for the cache subnet group"
}

variable "app_security_group_id" {
  type        = string
  description = "Security group ID of the ECS application tasks allowed to connect"
}

variable "node_type" {
  type        = string
  description = "Cache node instance type"
  default     = "cache.t4g.micro"
}
