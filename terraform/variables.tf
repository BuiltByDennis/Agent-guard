variable "project_id" {
  description = "The GCP Project ID"
  type        = string
}

variable "region" {
  description = "The GCP Region"
  type        = string
  default     = "us-central1"
}

variable "db_password" {
  description = "Database password for Postgres"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT Secret Key"
  type        = string
  sensitive   = true
}

variable "openai_api_key" {
  description = "OpenAI API Key"
  type        = string
  sensitive   = true
}

variable "image_url" {
  description = "The Docker image URL for the backend"
  type        = string
}

variable "frontend_url" {
  description = "The allowed CORS origin URL for the frontend"
  type        = string
  default     = "https://your-frontend-domain.com"
}
