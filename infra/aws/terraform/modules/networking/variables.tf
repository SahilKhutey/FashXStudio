variable "environment" {
  type        = string
  description = "Deployment environment name (dev, staging, prod)"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "Availability zones in the target region (ap-south-1)"
  default     = ["ap-south-1a", "ap-south-1b"]
}

variable "public_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for public subnets"
  default     = ["10.0.1.0/24", "10.0.2.0/24"]
}

variable "private_app_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private application subnets (ECS tasks)"
  default     = ["10.0.11.0/24", "10.0.12.0/24"]
}

variable "private_data_subnet_cidrs" {
  type        = list(string)
  description = "CIDR blocks for private data subnets (RDS, ElastiCache)"
  default     = ["10.0.21.0/24", "10.0.22.0/24"]
}
