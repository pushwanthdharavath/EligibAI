#!/bin/bash

# EligibAI AWS Deployment Script
# This script automates the deployment process

set -e

echo "Starting EligibAI AWS Deployment..."

# Check AWS CLI is installed
if ! command -v aws &> /dev/null; then
    echo "AWS CLI not found. Installing..."
    curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
    unzip awscliv2.zip
    sudo ./aws/install
fi

# Check Terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Terraform not found. Installing..."
    wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg
    echo "deb [signed-by=/usr/share/keyrings/hashicorp-archive-keyring.gpg] https://apt.releases.hashicorp.com $(lsb_release -cs) main" | sudo tee /etc/apt/sources.list.d/hashicorp.list
    sudo apt update && sudo apt install terraform
fi

# Navigate to Terraform directory
cd "$(dirname "$0")"

# Initialize Terraform
echo "Initializing Terraform..."
terraform init

# Plan the deployment
echo "Planning deployment..."
terraform plan -out=tfplan

# Apply the deployment
echo "Applying deployment..."
terraform apply -auto-approve tfplan

# Get outputs
echo "Getting deployment outputs..."
terraform output -json > outputs.json

echo "Deployment completed successfully!"
echo "Load Balancer DNS: $(terraform output alb_dns)"
echo "Database Endpoint: $(terraform output db_endpoint)"
echo "Redis Endpoint: $(terraform output redis_endpoint)"