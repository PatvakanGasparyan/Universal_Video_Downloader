# ☁️ AWS Deployment Guide

Deploy **Universal Video Downloader** on AWS using the bundled **Terraform** (EC2 + S3 + IAM + VPC), **k3s**, and **GitHub Actions**.

## 📑 Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Option A — Terraform (recommended)](#option-a--terraform-recommended)
- [Option B — Manual EC2](#option-b--manual-ec2)
- [Security Groups & port 8000](#security-groups--port-8000)
- [Elastic IP](#elastic-ip)
- [S3 storage](#s3-storage)
- [CI/CD with GitHub Actions](#cicd-with-github-actions)
- [Domain, HTTPS, Nginx & SSL](#domain-https-nginx--ssl)
- [Costs](#costs)
- [Teardown](#teardown)

---

## Architecture

See the [AWS Deployment diagram](ARCHITECTURE.md#aws-deployment). In short: GitHub Actions builds the image, pushes it to **GHCR**, then SSHes into an **EC2** instance running **k3s**, which pulls the image and (optionally) writes finished files to **S3** via an **IAM role**.

---

## Prerequisites

- AWS account + IAM user with programmatic access
- [Terraform](https://developer.hashicorp.com/terraform/downloads) ≥ 1.5
- An SSH key pair in your target region
- AWS CLI configured (`aws configure`)

---

## Option A — Terraform (recommended)

```bash
cd terraform
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
aws_region        = "eu-north-1"
project_name      = "universal-video-downloader"
instance_type     = "t3.micro"
ssh_key_name      = "your-keypair-name"
allowed_ssh_cidr  = "YOUR.IP.ADDR.0/32"   # tighten this!
allowed_app_cidr  = "0.0.0.0/0"
```

```bash
terraform init
terraform plan
terraform apply
```

Outputs include the **EC2 public IP** and the **S3 bucket name**. Open:

```
http://<EC2_PUBLIC_IP>:8000
```

> Replace `<EC2_PUBLIC_IP>` with the value Terraform prints (or your Elastic IP).

---

## Option B — Manual EC2

1. Launch an **Ubuntu 22.04/24.04** instance (`t3.micro` is enough for light use).
2. SSH in and install Docker or k3s.
3. Follow **[DEPLOYMENT.md](DEPLOYMENT.md)** (Docker Compose or systemd).
4. Open port **8000** in the Security Group (below).

---

## Security Groups & port 8000

> [!IMPORTANT]
> The #1 reason "I can't reach the site" — the Security Group blocks port 8000.

Add inbound rules:

| Type | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| SSH | TCP | 22 | *your IP*/32 | Admin |
| Custom TCP | TCP | 8000 | 0.0.0.0/0 | App |
| HTTP | TCP | 80 | 0.0.0.0/0 | Optional (Nginx) |
| HTTPS | TCP | 443 | 0.0.0.0/0 | Optional (TLS) |

```bash
# CLI example
aws ec2 authorize-security-group-ingress \
  --group-id sg-xxxx --protocol tcp --port 8000 --cidr 0.0.0.0/0
```

---

## Elastic IP

A stopped/started EC2 instance gets a **new** public IP. Attach an **Elastic IP** so your URL never changes:

```bash
aws ec2 allocate-address --domain vpc
aws ec2 associate-address --instance-id i-xxxx --allocation-id eipalloc-xxxx
```

---

## S3 storage

Enable uploads of finished downloads to S3:

```env
S3_ENABLED=true
AWS_REGION=eu-north-1
AWS_S3_BUCKET=<bucket-from-terraform-output>
S3_PREFIX=downloads
S3_DELETE_LOCAL_AFTER_UPLOAD=true
```

> [!TIP]
> On EC2, prefer the **IAM role** (provisioned by Terraform) over static keys — then you can omit `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` entirely.

---

## CI/CD with GitHub Actions

`.github/workflows/deploy.yml` runs on push to **`master`**:

1. **build** — builds the Docker image and pushes to GHCR (with cache).
2. **deploy** — SSHes into EC2, ensures swap, pulls the new image into k3s, and rolls out `deployment/uvd-backend`.

Required repo **secrets**:

| Secret | Description |
|--------|-------------|
| `EC2_HOST` | Public IP / DNS of the instance |
| `IAM_USERNAME` | SSH username (e.g. `ubuntu`) |
| `EC2_SSH_KEY` | Private key for SSH |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` | For the app secret (if not using IAM role) |

---

## Domain, HTTPS, Nginx & SSL

1. Point a DNS **A record** at your Elastic IP.
2. Put Nginx in front (see **[DEPLOYMENT.md](DEPLOYMENT.md#reverse-proxy-nginx)**).
3. Issue a free certificate:
   ```bash
   sudo certbot --nginx -d your-domain.com
   ```
4. Update `CORS_ORIGINS` to your `https://` domain.

---

## Costs

A `t3.micro` (free-tier eligible) + an S3 bucket is typically **free or a few USD/month** for personal use. Watch S3 egress and storage if you enable uploads.

---

## Teardown

```bash
cd terraform
terraform destroy
```

> This deletes the EC2 instance, S3 bucket, IAM role, and VPC created by Terraform. Back up anything you need first.
