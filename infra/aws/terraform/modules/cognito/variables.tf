variable "environment" {
  description = "Deployment environment name (dev, staging, prod)"
  type        = string
}

variable "aws_account_id" {
  description = "AWS account identifier for resource naming and domain prefixes"
  type        = string
  default     = "000000000000"
}

variable "callback_urls" {
  description = "List of allowed OAuth callback URLs for the mobile app"
  type        = list(string)
  default     = ["fashx://auth/callback"]
}

variable "logout_urls" {
  description = "List of allowed OAuth logout URLs for the mobile app"
  type        = list(string)
  default     = ["fashx://auth/logout"]
}

variable "deletion_protection" {
  description = "Whether deletion protection is enabled on the User Pool"
  type        = string
  default     = "INACTIVE"
}
