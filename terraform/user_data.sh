#!/bin/bash
set -euxo pipefail

PROJECT_NAME="${project_name}"
AWS_REGION="${aws_region}"
S3_BUCKET="${s3_bucket}"

export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get upgrade -y

# Docker (required for k3s and local container builds)
apt-get install -y ca-certificates curl gnupg
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
usermod -aG docker ubuntu

# k3s single-node cluster
curl -sfL https://get.k3s.io | INSTALL_K3S_EXEC="--write-kubeconfig-mode 644" sh -

# App runtime directories
mkdir -p /opt/${PROJECT_NAME}
cat >/opt/${PROJECT_NAME}/env.template <<EOF
S3_ENABLED=true
AWS_REGION=${AWS_REGION}
AWS_S3_BUCKET=${S3_BUCKET}
S3_PREFIX=downloads
S3_DELETE_LOCAL_AFTER_UPLOAD=true
EOF

echo "EC2 bootstrap complete for ${PROJECT_NAME}" > /var/log/user-data-complete.log
