output "bucket_name" {
  value       = aws_s3_bucket.media.id
  description = "Name of the S3 media bucket"
}

output "bucket_arn" {
  value       = aws_s3_bucket.media.arn
  description = "ARN of the S3 media bucket"
}
