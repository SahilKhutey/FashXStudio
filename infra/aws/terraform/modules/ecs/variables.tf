variable "environment" {
  type        = string
  description = "Deployment environment name (dev, staging, prod)"
}

variable "vpc_id" {
  type        = string
  description = "VPC ID where ECS tasks are provisioned"
}

variable "private_app_subnet_ids" {
  type        = list(string)
  description = "Subnet IDs where ECS tasks will run"
}

variable "public_subnet_ids" {
  type        = list(string)
  description = "Public subnet IDs for the ALB"
}

variable "s3_bucket_arn" {
  type        = string
  description = "ARN of the private S3 media bucket"
}
