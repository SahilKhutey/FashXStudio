output "user_pool_id" {
  description = "Amazon Cognito User Pool ID"
  value       = aws_cognito_user_pool.users.id
}

output "user_pool_arn" {
  description = "Amazon Cognito User Pool ARN"
  value       = aws_cognito_user_pool.users.arn
}

output "user_pool_client_id" {
  description = "Amazon Cognito Public App Client ID"
  value       = aws_cognito_user_pool_client.mobile.id
}

output "user_pool_endpoint" {
  description = "Amazon Cognito User Pool Endpoint"
  value       = aws_cognito_user_pool.users.endpoint
}

output "issuer_url" {
  description = "Expected OIDC Issuer URL for JWT validation"
  value       = "https://${aws_cognito_user_pool.users.endpoint}"
}

output "jwks_url" {
  description = "Public JWKS URL for key retrieval and rotation"
  value       = "https://${aws_cognito_user_pool.users.endpoint}/.well-known/jwks.json"
}

output "cognito_domain" {
  description = "Cognito authentication domain prefix"
  value       = aws_cognito_user_pool_domain.auth_domain.domain
}
