# EligibAI Deployment Guide

This guide covers the complete deployment process for EligibAI using Docker and AWS.

## Prerequisites

- Docker and Docker Compose installed
- AWS CLI configured with appropriate credentials
- Terraform installed (for AWS deployment)
- Python 3.12+ and Node.js 18+ (for local development)

## Local Development Deployment

### Quick Start with Docker Compose

1. Clone the repository:
```bash
git clone <repository-url>
cd eligiblAI
```

2. Create environment file:
```bash
cp backend/.env.example backend/.env
```

3. Update environment variables in `backend/.env`:
```env
DATABASE_URL=postgresql://eligibai:eligibai_password@postgres:5432/eligibai
QDRANT_URL=http://qdrant:6333
QDRANT_COLLECTION_NAME=scholarships
REDIS_URL=redis://redis:6379
OPENAI_API_KEY=your_openai_api_key_here
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-base
```

4. Start all services:
```bash
docker-compose up -d
```

5. Verify services are running:
```bash
docker-compose ps
```

6. Access the application:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Qdrant Dashboard: http://localhost:6333/dashboard

### Manual Setup (Without Docker)

#### Backend Setup

1. Create virtual environment:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start the backend:
```bash
python main.py
```

#### Frontend Setup

1. Install dependencies:
```bash
cd frontend
npm install
```

2. Start the frontend:
```bash
npm run dev
```

#### Database Setup

1. Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql

# Windows
# Download from https://www.postgresql.org/download/windows/
```

2. Create database:
```sql
CREATE DATABASE eligibai;
CREATE USER eligibai WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE eligibai TO eligibai;
```

3. Update `DATABASE_URL` in backend `.env` file.

#### Qdrant Setup

1. Install Qdrant:
```bash
# Using Docker
docker run -p 6333:6333 qdrant/qdrant

# Or download from https://github.com/qdrant/qdrant/releases
```

2. Verify connection:
```bash
curl http://localhost:6333/collections
```

#### Redis Setup

1. Install Redis:
```bash
# Ubuntu/Debian
sudo apt-get install redis-server

# macOS
brew install redis

# Windows
# Download from https://github.com/microsoftarchive/redis/releases
```

2. Start Redis:
```bash
redis-server
```

## AWS Production Deployment

### Infrastructure Setup with Terraform

1. Configure AWS credentials:
```bash
aws configure
```

2. Navigate to Terraform directory:
```bash
cd aws/terraform
```

3. Initialize Terraform:
```bash
terraform init
```

4. Review the deployment plan:
```bash
terraform plan
```

5. Deploy infrastructure:
```bash
terraform apply
```

6. Save the outputs:
```bash
terraform output -json > outputs.json
```

### Application Deployment

#### Option 1: AWS ECS (Recommended)

1. Build and push Docker images:
```bash
# Backend
cd backend
docker build -t eligibai-backend .
docker tag eligibai-backend:latest <your-ecr-repo>/eligibai-backend:latest
docker push <your-ecr-repo>/eligibai-backend:latest

# Frontend
cd frontend
docker build -t eligibai-frontend .
docker tag eligibai-frontend:latest <your-ecr-repo>/eligibai-frontend:latest
docker push <your-ecr-repo>/eligibai-frontend:latest
```

2. Create ECS task definitions:
```bash
aws ecs register-task-definition --family eligibai-backend --cli-input-json file://backend-task-definition.json
aws ecs register-task-definition --family eligibai-frontend --cli-input-json file://frontend-task-definition.json
```

3. Create ECS services:
```bash
aws ecs create-service --cluster eligibai-cluster --service-name eligibai-backend --task-definition eligibai-backend --desired-count 2 --launch-type FARGATE
aws ecs create-service --cluster eligibai-cluster --service-name eligibai-frontend --task-definition eligibai-frontend --desired-count 2 --launch-type FARGATE
```

#### Option 2: AWS EC2

1. Launch EC2 instances:
```bash
aws ec2 run-instances --image-id ami-xxxxx --instance-type t3.medium --key-name your-key --security-group-ids sg-xxxxx --subnet-id subnet-xxxxx
```

2. SSH into instances:
```bash
ssh -i your-key.pem ubuntu@<instance-ip>
```

3. Install Docker:
```bash
sudo apt-get update
sudo apt-get install docker.io docker-compose
sudo usermod -aG docker ubuntu
```

4. Deploy with Docker Compose:
```bash
git clone <repository-url>
cd eligiblAI
docker-compose up -d
```

### Environment Configuration

Set the following environment variables in AWS ECS or EC2:

```env
DATABASE_URL=postgresql://eligibai:password@<db-endpoint>:5432/eligibai
QDRANT_URL=http://<qdrant-endpoint>:6333
QDRANT_COLLECTION_NAME=scholarships
REDIS_URL=redis://<redis-endpoint>:6379
OPENAI_API_KEY=your_production_api_key
EMBEDDING_MODEL=BAAI/bge-m3
RERANKER_MODEL=BAAI/bge-reranker-base
```

### Load Balancer Configuration

1. Configure ALB listeners to forward traffic:
- Port 80 → Frontend (port 3000)
- Port 8000 → Backend (port 8000)

2. Set up health checks:
- Frontend: GET / every 30 seconds
- Backend: GET /health every 30 seconds

3. Configure SSL/TLS:
- Add HTTPS listener on port 443
- Use ACM certificates for SSL termination

### Monitoring and Logging

1. Enable CloudWatch logs:
```bash
aws logs create-log-group --log-group-name /ecs/eligibai-backend
aws logs create-log-group --log-group-name /ecs/eligibai-frontend
```

2. Set up CloudWatch alarms:
- CPU utilization > 80%
- Memory utilization > 85%
- 5xx error rate > 1%

3. Enable X-Ray tracing for distributed tracing

## CI/CD Pipeline

### GitHub Actions Example

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to AWS

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Configure AWS credentials
        uses: aws-actions/configure-aws-credentials@v1
        with:
          aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY_ID }}
          aws-secret-access-key: ${{ secrets.AWS_SECRET_ACCESS_KEY }}
          aws-region: us-east-1
      
      - name: Build and push backend
        run: |
          cd backend
          docker build -t eligibai-backend .
          docker push ${{ secrets.ECR_REPO }}/eligibai-backend:latest
      
      - name: Build and push frontend
        run: |
          cd frontend
          docker build -t eligibai-frontend .
          docker push ${{ secrets.ECR_REPO }}/eligibai-frontend:latest
      
      - name: Deploy to ECS
        run: |
          aws ecs update-service --cluster eligibai-cluster --service eligibai-backend --force-new-deployment
          aws ecs update-service --cluster eligibai-cluster --service eligibai-frontend --force-new-deployment
```

## Post-Deployment Steps

1. Index scholarships in Qdrant:
```bash
curl -X POST http://<backend-url>/api/index
```

2. Run system evaluation:
```bash
curl -X POST http://<backend-url>/api/evaluation/run
```

3. Monitor system health:
```bash
curl http://<backend-url>/health
curl http://<frontend-url>/
```

4. Check application logs:
```bash
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Troubleshooting

### Backend Issues

- **Database connection errors**: Check DATABASE_URL and ensure PostgreSQL is running
- **Qdrant connection errors**: Verify Qdrant is accessible and QDRANT_URL is correct
- **Model loading errors**: Ensure sufficient memory and proper model paths

### Frontend Issues

- **Build failures**: Check Node.js version and dependencies
- **API connection errors**: Verify CORS settings and backend URL
- **Deployment issues**: Check Docker logs and environment variables

### AWS Issues

- **Infrastructure deployment**: Check Terraform state and AWS credentials
- **ECS task failures**: Review CloudWatch logs and task definitions
- **Load balancer issues**: Verify target groups and health checks

## Scaling Considerations

### Horizontal Scaling

- **Backend**: Increase ECS tasks based on CPU/memory metrics
- **Frontend**: Use Auto Scaling groups for EC2 or ECS
- **Database**: Use RDS read replicas for read-heavy workloads

### Vertical Scaling

- **Backend**: Upgrade instance types (t3.medium → t3.large → m5.large)
- **Database**: Increase RDS instance class and storage
- **Cache**: Upgrade ElastiCache node types

### Cost Optimization

- Use Spot instances for non-critical workloads
- Enable Reserved Instances for predictable workloads
- Implement auto-scaling to scale down during low traffic
- Use CloudWatch Cost Explorer to monitor spending

## Security Best Practices

1. **Environment Variables**: Never commit sensitive data to git
2. **IAM Roles**: Use least-privilege IAM policies
3. **Network Security**: Use security groups and VPC endpoints
4. **Encryption**: Enable encryption for EBS volumes and RDS
5. **Secrets Management**: Use AWS Secrets Manager for sensitive data
6. **SSL/TLS**: Always use HTTPS in production
7. **Container Security**: Scan images for vulnerabilities
8. **Monitoring**: Enable CloudTrail for audit logging

## Backup and Recovery

1. **Database Backups**: Enable automated RDS backups
2. **Code Backups**: Use ECR for Docker images
3. **Configuration Backups**: Store Terraform state in S3
4. **Disaster Recovery**: Set up multi-region deployment

## Performance Tuning

1. **Database**: Enable connection pooling, optimize queries
2. **Cache**: Implement Redis caching for frequently accessed data
3. **CDN**: Use CloudFront for static assets
4. **Load Balancing**: Distribute traffic across multiple instances
5. **Monitoring**: Use CloudWatch Insights for performance metrics

## Maintenance

1. **Regular Updates**: Keep dependencies and base images updated
2. **Log Rotation**: Implement log rotation to prevent disk space issues
3. **Health Checks**: Monitor application health continuously
4. **Performance Reviews**: Regular performance audits and optimization
5. **Security Audits**: Regular security assessments and updates