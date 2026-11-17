variable "environment" {
  type        = string
  description = "Deployment environment name (dev, staging, prod)"
}

variable "alarm_email" {
  type        = string
  description = "Operator email address for SNS operational alerts"
  default     = "operations@fashxstudio.com"
}
