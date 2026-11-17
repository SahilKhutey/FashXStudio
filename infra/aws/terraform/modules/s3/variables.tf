variable "environment" {
  type        = string
  description = "Deployment environment name (dev, staging, prod)"
}

variable "account_id" {
  type        = string
  description = "AWS Account ID for bucket naming uniqueness"
}
