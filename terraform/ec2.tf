resource "aws_security_group" "app" {
  name        = "${local.name_prefix}-sg"
  description = "Security group for video downloader EC2 / k3s node"
  vpc_id      = aws_vpc.main.id

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.allowed_ssh_cidr]
  }

  ingress {
    description = "HTTP"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = [var.allowed_app_cidr]
  }

  ingress {
    description = "HTTPS"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = [var.allowed_app_cidr]
  }

  ingress {
    description = "FastAPI app (dev)"
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = [var.allowed_app_cidr]
  }

  ingress {
    description = "k3s API"
    from_port   = 6443
    to_port     = 6443
    protocol    = "tcp"
    cidr_blocks = [var.allowed_app_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-sg"
  })
}

resource "aws_instance" "app" {
  ami                         = data.aws_ami.ubuntu.id
  instance_type               = var.instance_type
  key_name                    = var.ssh_key_name
  subnet_id                   = aws_subnet.public.id
  vpc_security_group_ids      = [aws_security_group.app.id]
  iam_instance_profile        = aws_iam_instance_profile.ec2_app.name
  associate_public_ip_address = true

  root_block_device {
    volume_size = var.ec2_volume_size_gb
    volume_type = "gp3"
    encrypted   = true
  }

  user_data = templatefile("${path.module}/user_data.sh", {
    project_name = var.project_name
    PROJECT_NAME = var.project_name
    aws_region   = var.aws_region
    AWS_REGION   = var.aws_region
    s3_bucket    = aws_s3_bucket.videos.bucket
    S3_BUCKET    = aws_s3_bucket.videos.bucket
  })
  metadata_options {
    http_endpoint = "enabled"
    http_tokens   = "required"
  }

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-ec2"
  })
}
