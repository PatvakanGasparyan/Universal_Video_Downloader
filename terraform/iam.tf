resource "aws_iam_role" "ec2_app" {
  name = "${local.name_prefix}-ec2-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Principal = {
          Service = "ec2.amazonaws.com"
        }
        Action = "sts:AssumeRole"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_policy" "s3_upload" {
  name        = "${local.name_prefix}-s3-upload"
  description = "Allow the video downloader app to upload files to S3"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid    = "ListBucket"
        Effect = "Allow"
        Action = [
          "s3:ListBucket"
        ]
        Resource = aws_s3_bucket.videos.arn
      },
      {
        Sid    = "ObjectAccess"
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:AbortMultipartUpload",
          "s3:ListMultipartUploadParts"
        ]
        Resource = "${aws_s3_bucket.videos.arn}/*"
      }
    ]
  })

  tags = local.common_tags
}

resource "aws_iam_role_policy_attachment" "ec2_s3_upload" {
  role       = aws_iam_role.ec2_app.name
  policy_arn = aws_iam_policy.s3_upload.arn
}

resource "aws_iam_instance_profile" "ec2_app" {
  name = "${local.name_prefix}-ec2-profile"
  role = aws_iam_role.ec2_app.name
}
