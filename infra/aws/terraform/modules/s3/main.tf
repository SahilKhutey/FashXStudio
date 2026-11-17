# Amazon S3 Private Storage Module — ap-south-1

resource "aws_s3_bucket" "media" {
  bucket        = "fashx-${var.environment}-private-${var.account_id}"
  force_destroy = var.environment == "prod" ? false : true

  tags = {
    Name        = "fashx-${var.environment}-private-${var.account_id}"
    Environment = var.environment
  }
}

resource "aws_s3_bucket_ownership_controls" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}

resource "aws_s3_bucket_public_access_block" "media" {
  bucket = aws_s3_bucket.media.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# Lifecycle rule for temporary staging/validation files
resource "aws_s3_bucket_lifecycle_configuration" "media" {
  bucket = aws_s3_bucket.media.id

  rule {
    id     = "expire-temporary-validation"
    status = "Enabled"

    filter {
      prefix = "temporary/"
    }

    expiration {
      days = 1
    }
  }
}
