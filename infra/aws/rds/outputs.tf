output "database_endpoints" {
  description = "Private PostgreSQL endpoints by environment."

  value = {
    for environment, db in aws_db_instance.database :
    environment => {
      address = db.address
      port    = db.port
      db_name = db.db_name
    }
  }
}

output "database_security_groups" {
  description = "Security group IDs protecting database instances by environment."

  value = {
    for environment, sg in aws_security_group.database :
    environment => sg.id
  }
}

output "master_secret_arns" {
  description = "RDS-managed master credentials secret ARNs."

  value = {
    for environment, db in aws_db_instance.database :
    environment => db.master_user_secret[0].secret_arn
  }
  sensitive = true
}
