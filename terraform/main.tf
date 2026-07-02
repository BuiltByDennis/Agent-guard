terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# --- VPC & Networking ---
resource "google_compute_network" "vpc" {
  name                    = "agent-proxy-vpc"
  auto_create_subnetworks = false
}

resource "google_compute_subnetwork" "subnet" {
  name          = "agent-proxy-subnet"
  ip_cidr_range = "10.0.1.0/24"
  network       = google_compute_network.vpc.id
  region        = var.region
}

resource "google_vpc_access_connector" "connector" {
  name          = "agent-proxy-connector"
  region        = var.region
  subnet {
    name = google_compute_subnetwork.subnet.name
  }
  machine_type  = "e2-micro"
}

# --- Cloud SQL (PostgreSQL) ---
resource "google_sql_database_instance" "postgres" {
  name             = "agent-proxy-db"
  database_version = "POSTGRES_15"
  region           = var.region

  settings {
    tier = "db-f1-micro"
    ip_configuration {
      ipv4_enabled    = true
      private_network = google_compute_network.vpc.id
    }
  }
}

resource "google_sql_database" "database" {
  name     = "proxy_db"
  instance = google_sql_database_instance.postgres.name
}

resource "google_sql_user" "users" {
  name     = "postgres"
  instance = google_sql_database_instance.postgres.name
  password = var.db_password
}

# --- Memorystore (Redis) ---
resource "google_redis_instance" "redis" {
  name           = "agent-proxy-redis"
  tier           = "BASIC"
  memory_size_gb = 1
  region         = var.region
  authorized_network = google_compute_network.vpc.id
}

# --- Secret Manager ---
resource "google_secret_manager_secret" "jwt_secret" {
  secret_id = "agent-proxy-jwt-secret"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "jwt_secret_version" {
  secret = google_secret_manager_secret.jwt_secret.id
  secret_data = var.jwt_secret_key
}

resource "google_secret_manager_secret" "openai_api_key" {
  secret_id = "agent-proxy-openai-api-key"
  replication {
    auto {}
  }
}

resource "google_secret_manager_secret_version" "openai_api_key_version" {
  secret = google_secret_manager_secret.openai_api_key.id
  secret_data = var.openai_api_key
}

# --- Cloud Run ---
resource "google_cloud_run_v2_service" "backend" {
  name     = "agent-proxy-backend"
  location = var.region

  template {
    containers {
      image = var.image_url

      env {
        name  = "DATABASE_URL"
        value = "postgresql+asyncpg://postgres:${var.db_password}@${google_sql_database_instance.postgres.private_ip_address}/proxy_db"
      }
      env {
        name  = "REDIS_URL"
        value = "redis://${google_redis_instance.redis.host}:${google_redis_instance.redis.port}/0"
      }
      env {
        name  = "FRONTEND_URL"
        value = var.frontend_url
      }
      env {
        name  = "FIREWALL_MODE"
        value = "BLOCK"
      }
      env {
        name = "JWT_SECRET_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.jwt_secret.secret_id
            version = "latest"
          }
        }
      }
      env {
        name = "OPENAI_API_KEY"
        value_source {
          secret_key_ref {
            secret  = google_secret_manager_secret.openai_api_key.secret_id
            version = "latest"
          }
        }
      }
    }
    vpc_access {
      connector = google_vpc_access_connector.connector.id
      egress    = "ALL_TRAFFIC"
    }
  }
}
