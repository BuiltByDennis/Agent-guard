output "cloud_run_url" {
  description = "The URL of the deployed Cloud Run service"
  value       = google_cloud_run_v2_service.backend.uri
}

output "redis_host" {
  description = "The internal IP of the Redis instance"
  value       = google_redis_instance.redis.host
}

output "db_private_ip" {
  description = "The private IP address of the Cloud SQL instance"
  value       = google_sql_database_instance.postgres.private_ip_address
}
