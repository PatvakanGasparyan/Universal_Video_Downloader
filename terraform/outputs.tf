output "s3_bucket_name" {
  description = "Name of the S3 bucket for video storage"
  value       = aws_s3_bucket.videos.bucket
}

output "s3_bucket_arn" {
  description = "ARN of the S3 bucket"
  value       = aws_s3_bucket.videos.arn
}

output "ec2_public_ip" {
  description = "Public IP of the application EC2 instance"
  value       = aws_instance.app.public_ip
}

output "ec2_instance_id" {
  description = "EC2 instance ID"
  value       = aws_instance.app.id
}

output "iam_role_name" {
  description = "IAM role attached to the EC2 instance"
  value       = aws_iam_role.ec2_app.name
}

output "app_env_template" {
  description = "Suggested environment variables for the application"
  value = {
    S3_ENABLED                   = "true"
    AWS_REGION                   = var.aws_region
    AWS_S3_BUCKET                = aws_s3_bucket.videos.bucket
    S3_PREFIX                    = "downloads"
    S3_DELETE_LOCAL_AFTER_UPLOAD = "true"
  }
}
