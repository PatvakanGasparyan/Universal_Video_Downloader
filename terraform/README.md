# Terraform — AWS Infrastructure

Provisions the cloud foundation for **Universal Video Downloader**:

- **S3 bucket** — stores downloaded videos
- **IAM role + policy** — grants EC2 permission to upload to S3 (no hard-coded keys on the server)
- **EC2 (Ubuntu 22.04)** — hosts k3s and the application
- **VPC + security group** — networking and firewall rules

## Prerequisites

- [Terraform](https://www.terraform.io/downloads) >= 1.5
- AWS account with credentials configured (`aws configure`)
- An existing EC2 key pair in your target region

## Quick start

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars — set ssh_key_name and allowed_ssh_cidr

terraform init
terraform plan
terraform apply
```

## Outputs

After `terraform apply`:

```bash
terraform output s3_bucket_name
terraform output ec2_public_ip
terraform output app_env_template
```

Use `app_env_template` values in your `.env` or Kubernetes ConfigMap. On EC2, the IAM instance profile provides AWS credentials automatically — leave `AWS_ACCESS_KEY_ID` empty.

## Destroy

```bash
terraform destroy
```

**Warning:** This deletes the S3 bucket and all stored videos unless you enable `force_destroy` (not enabled by default for safety).
