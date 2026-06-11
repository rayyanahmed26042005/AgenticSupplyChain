# terraform/variables.tf

variable "aws_region" {
  type        = string
  description = "The target AWS Region for all resources"
  default     = "us-east-1"
}

variable "ubuntu_ami_id" {
  type        = string
  description = "Ubuntu Server 22.04 LTS AMI ID"
  # Clean default AMI for Ubuntu 22.04 in us-east-1 (x86_64)
  default     = "ami-0fc5d935ebf8bc3bc"
}

variable "ssh_public_key" {
  type        = string
  description = "The SSH Public Key content for EC2 instance access"
}

variable "s3_bucket_name" {
  type        = string
  description = "A unique bucket name for the static frontend React build assets"
  default     = "supply-chain-frontend-bucket-prod-26042005"
}

variable "db_password" {
  type        = string
  description = "Password for the RDS PostgreSQL database"
  sensitive   = true
}

variable "mongodb_uri" {
  type        = string
  description = "Connection URI for MongoDB Atlas Cluster"
  sensitive   = true
}

variable "groq_api_key" {
  type        = string
  description = "Groq API Key for LLM-based agent decisions"
  sensitive   = true
}
