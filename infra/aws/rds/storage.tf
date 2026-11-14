# ==============================================================================
# FASHXSTUDIO — S3 PRIVATE MEDIA STORAGE INFRASTRUCTURE
# ==============================================================================

data "aws_caller_identity" "current" {}

locals {
  fashx_buckets = {
    dev     = "fashx-dev-private-${data.aws_caller_identity.current.account_id}"
    staging = "fashx-staging-private-${data.aws_caller_identity.current.account_id}"
    prod    = "fashx-prod-private-${data.aws_caller_identity.current.account_id}"
  }
}

resource "aws_s3_bucket" "private_media" {
  for_each      = local.fashx_buckets
  bucket        = each.value
  force_destroy = false

  tags = {
    Project     = "FashXStudio"
    Environment = each.key
    DataClass   = each.key == "prod" ? "sensitive-user-media" : "non-production"
  }
}

resource "aws_s3_bucket_public_access_block" "private_media" {
  for_each = aws_s3_bucket.private_media

  bucket                  = each.value.id
  block_public_acls       = true
  ignore_public_acls      = true
  block_public_policy     = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "private_media" {
  for_each = aws_s3_bucket.private_media

  bucket = each.value.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "private_media" {
  for_each = aws_s3_bucket.private_media

  bucket = each.value.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_policy" "require_tls" {
  for_each = aws_s3_bucket.private_media

  bucket = each.value.id
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "DenyInsecureTransport"
        Effect    = "Deny"
        Principal = "*"
        Action    = "s3:*"
        Resource = [
          each.value.arn,
          "${each.value.arn}/*"
        ]
        Condition = {
          Bool = {
            "aws:SecureTransport" = "false"
          }
        }
      }
    ]
  })

  depends_on = [
    aws_s3_bucket_public_access_block.private_media
  ]
}

resource "aws_s3_bucket_lifecycle_configuration" "private_media" {
  for_each = aws_s3_bucket.private_media

  bucket = each.value.id

  rule {
    id     = "abort-incomplete-multipart-uploads"
    status = "Enabled"

    filter {}

    abort_incomplete_multipart_upload {
      days_after_initiation = 7
    }
  }

  rule {
    id     = "temporary-object-expiration"
    status = "Enabled"

    filter {
      prefix = "temporary/"
    }

    expiration {
      days = 7
    }
  }
}

output "fashx_s3_buckets" {
  description = "Private S3 media bucket names by environment"
  value = {
    for env, bucket in aws_s3_bucket.private_media : env => bucket.bucket
  }
}
