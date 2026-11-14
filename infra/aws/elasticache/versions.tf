terraform {
  required_version = ">= 1.10.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.80, < 7.0"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6.0"
    }
  }

  backend "s3" {
    bucket       = "REPLACE_WITH_YOUR_TERRAFORM_STATE_BUCKET"
    key          = "fashx/phase-03-03/elasticache/terraform.tfstate"
    region       = "ap-south-1"
    encrypt      = true
    use_lockfile = true
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project    = "FashXStudio"
      ManagedBy  = "Terraform"
      Phase      = "03.3"
      CostCenter = "FashX"
    }
  }
}
