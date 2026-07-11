variable "aws_region" {
  description = "AWS region for all resources"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name used for resource naming"
  type        = string
  default     = "universal-video-downloader"
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "instance_type" {
  description = "EC2 instance type for the k3s node"
  type        = string
  default     = "t3.medium"
}

variable "ssh_key_name" {
  description = "Existing AWS EC2 key pair name for SSH access"
  type        = string
}

variable "allowed_ssh_cidr" {
  description = "CIDR block allowed to SSH into the EC2 instance"
  type        = string
  default     = "0.0.0.0/0"
}

variable "allowed_app_cidr" {
  description = "CIDR block allowed to reach the application"
  type        = string
  default     = "0.0.0.0/0"
}

variable "ec2_volume_size_gb" {
  description = "Root EBS volume size in GB"
  type        = number
  default     = 40
}
