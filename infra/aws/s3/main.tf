terraform {
  required_version = ">= 1.6.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "bucket_prefix" {
  type    = string
  default = "fashx"
}

variable "environments" {
  type    = set(string)
  default = ["dev", "staging", "prod"]
  validation {
    condition = alltrue([
      for env in var.environments : contains(["dev", "staging", "prod"], env)
    ])
    error_message = "Only dev, staging and prod are supported."
  }
}

data "aws_caller_identity" "current" {}

locals {
  buckets = {
    for env in var.environments : env => "${var.bucket_prefix}-${env}-private-${data.aws_caller_identity.current.account_id}"
  }
}

# One customer-managed encryption key per environment
resource "aws_kms_key" "media" {
  for_each                = var.environments
  description             = "FashXStudio ${each.key} S3 media encryption"
  enable_key_rotation     = true
  deletion_window_in_days = 30

  tags = {
    Project     = "FashXStudio"
    Environment = each.key
    ManagedBy   = "Terraform"
  }
}

resource "aws_kms_alias" "media" {
  for_each      = var.environments
  name          = "alias/fashx-${each.key}-s3"
  target_key_id = aws_kms_key.media[each.key].key_id
}

resource "aws_s3_bucket" "media" {
  for_each      = local.buckets
  bucket        = each.value
  force_destroy = false

  tags = {
    Project     = "FashXStudio"
    Environment = each.key
    DataClass   = "private-media"
    ManagedBy   = "Terraform"
  }

  lifecycle {
    prevent_destroy = true
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  for_each                = local.buckets
  bucket                  = aws_s3_bucket.media[each.key].id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "media" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.media[each.key].id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.media[each.key].id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm     = "aws:kms"
      kms_master_key_id = aws_kms_key.media[each.key].arn
    }
    bucket_key_enabled = true
  }
}

# Versioning remains disabled in this initial design.
# This makes ordinary DeleteObject operations permanently remove
# the current object rather than only adding a delete marker.
resource "aws_s3_bucket_lifecycle_configuration" "media" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.media[each.key].id

  rule {
    id     = "expire-temporary-objects"
    status = "Enabled"

    filter {
      prefix = "temporary/"
    }

    expiration {
      days = 1
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  rule {
    id     = "expire-old-vto-results"
    status = "Enabled"

    filter {
      prefix = "tryon/"
    }

    expiration {
      days = 30
    }

    abort_incomplete_multipart_upload {
      days_after_initiation = 1
    }
  }

  # Do not automatically expire users/ or products/.
  # Their retention depends on consent, user deletion and
  # merchant licensing/contractual requirements.
}

resource "aws_s3_bucket_policy" "media" {
  for_each = local.buckets
  bucket   = aws_s3_bucket.media[each.key].id

  depends_on = [
    aws_s3_bucket_public_access_block.media
  ]

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          aws_s3_bucket.media[each.key].arn,
          "${aws_s3_bucket.media[each.key].arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })
}

output "bucket_names" {
  value = { for env, bucket in aws_s3_bucket.media : env => bucket.bucket }
}

output "kms_key_arns" {
  value = { for env, key in aws_kms_key.media : env => key.arn }
}
