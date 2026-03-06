# =============================================================================
# DebtSense — Production Environment
# =============================================================================
# Calls the core infrastructure module with production-grade values.
#
# Usage:
#   cd infrastructure/terraform/environments/prod
#   terraform init
#   terraform plan -var-file="terraform.tfvars"
#   terraform apply -var-file="terraform.tfvars"
# =============================================================================

terraform {
  required_version = ">= 1.5"

  # Remote state — S3 backend with DynamoDB locking
  backend "s3" {
    bucket         = "debtsense-terraform-state"
    key            = "prod/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "debtsense-terraform-locks"
  }

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  default_tags {
    tags = {
      Project     = "debtsense"
      Environment = "prod"
      ManagedBy   = "terraform"
    }
  }
}

# =============================================================================
# Variables (override via terraform.tfvars or CI/CD pipeline)
# =============================================================================

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "db_password" {
  description = "PostgreSQL master password"
  type        = string
  sensitive   = true
}

variable "jwt_secret_key" {
  description = "JWT secret key"
  type        = string
  sensitive   = true
}

variable "encryption_key" {
  description = "Data encryption key"
  type        = string
  sensitive   = true
}

variable "backend_image" {
  description = "Backend Docker image URI"
  type        = string
}

variable "frontend_image" {
  description = "Frontend Docker image URI"
  type        = string
}

variable "domain_name" {
  description = "Production domain name"
  type        = string
  default     = "app.debtsense.io"
}

variable "certificate_arn" {
  description = "ACM certificate ARN for the domain"
  type        = string
}

# =============================================================================
# Module invocation
# =============================================================================

module "debtsense" {
  source = "../../modules"

  environment = "prod"
  aws_region  = var.aws_region

  # --- Networking ---
  vpc_cidr           = "10.0.0.0/16"
  availability_zones = ["us-east-1a", "us-east-1b", "us-east-1c"]

  # --- Database (production-grade) ---
  db_instance_class    = "db.r6g.large"
  db_allocated_storage = 100
  db_name              = "debtsense"
  db_username          = "debtsense_admin"
  db_password          = var.db_password

  # --- Redis (production-grade with replica) ---
  redis_node_type       = "cache.r6g.large"
  redis_num_cache_nodes = 2

  # --- ECS / Fargate ---
  backend_image  = var.backend_image
  frontend_image = var.frontend_image

  backend_cpu    = 1024  # 1 vCPU
  backend_memory = 2048  # 2 GB
  frontend_cpu   = 512   # 0.5 vCPU
  frontend_memory = 1024  # 1 GB

  backend_desired_count  = 3
  frontend_desired_count = 2

  # --- Domain and TLS ---
  domain_name     = var.domain_name
  certificate_arn = var.certificate_arn

  # --- Secrets ---
  jwt_secret_key = var.jwt_secret_key
  encryption_key = var.encryption_key
}

# =============================================================================
# Outputs
# =============================================================================

output "alb_dns_name" {
  description = "ALB DNS name — point your domain CNAME here"
  value       = module.debtsense.alb_dns_name
}

output "rds_endpoint" {
  description = "RDS writer endpoint"
  value       = module.debtsense.rds_endpoint
}

output "rds_reader_endpoint" {
  description = "RDS reader endpoint (for read replicas)"
  value       = module.debtsense.rds_reader_endpoint
}

output "redis_endpoint" {
  description = "Redis primary endpoint"
  value       = module.debtsense.redis_endpoint
}

output "ecs_cluster" {
  description = "ECS cluster name"
  value       = module.debtsense.ecs_cluster_name
}
