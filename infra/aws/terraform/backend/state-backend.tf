# Terraform Remote State Backend Specification
# Region: ap-south-1 (Mumbai)

terraform {
  required_version = ">= 1.7.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.40"
    }
  }

  backend "s3" {
    bucket         = "fashx-terraform-state-ap-south-1"
    key            = "fashx/terraform.tfstate"
    region         = "ap-south-1"
    dynamodb_table = "fashx-terraform-locks"
    encrypt        = true
  }
}
