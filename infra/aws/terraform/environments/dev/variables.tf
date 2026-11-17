variable "aws_region" {
  type        = string
  description = "AWS region for deployment"
  default     = "ap-south-1"
}

variable "environment" {
  type        = string
  description = "Deployment environment"
  default     = "dev"
}

variable "account_id" {
  type        = string
  description = "AWS Account ID"
  default     = "123456789012"
}
