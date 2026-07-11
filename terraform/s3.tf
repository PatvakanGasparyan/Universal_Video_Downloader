resource "aws_s3_bucket" "videos" {
  bucket = "${local.name_prefix}-videos-${data.aws_caller_identity.current.account_id}"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-videos"
  })
}

resource "aws_s3_bucket_versioning" "videos" {
  bucket = aws_s3_bucket.videos.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

resource "aws_s3_bucket_public_access_block" "videos" {
  bucket = aws_s3_bucket.videos.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_lifecycle_configuration" "videos" {
  bucket = aws_s3_bucket.videos.id

  rule {
      id     = "auto-delete-old-videos"
      status = "Enabled"

      filter {
        prefix = ""
      }

      expiration {
        days = 1
      }
    }
}

data "aws_caller_identity" "current" {}
