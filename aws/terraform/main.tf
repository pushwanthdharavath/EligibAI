# AWS Infrastructure for EligibAI
# This Terraform configuration sets up the necessary AWS resources

provider "aws" {
  region = var.aws_region
}

# VPC
resource "aws_vpc" "eligibai_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "eligibai-vpc"
    Environment = "production"
  }
}

# Public Subnets
resource "aws_subnet" "public_subnet_1" {
  vpc_id                  = aws_vpc.eligibai_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "eligibai-public-subnet-1"
    Environment = "production"
  }
}

resource "aws_subnet" "public_subnet_2" {
  vpc_id                  = aws_vpc.eligibai_vpc.id
  cidr_block              = "10.0.2.0/24"
  availability_zone       = "us-east-1b"
  map_public_ip_on_launch = true

  tags = {
    Name = "eligibai-public-subnet-2"
    Environment = "production"
  }
}

# Private Subnets
resource "aws_subnet" "private_subnet_1" {
  vpc_id            = aws_vpc.eligibai_vpc.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "us-east-1a"

  tags = {
    Name = "eligibai-private-subnet-1"
    Environment = "production"
  }
}

resource "aws_subnet" "private_subnet_2" {
  vpc_id            = aws_vpc.eligibai_vpc.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "us-east-1b"

  tags = {
    Name = "eligibai-private-subnet-2"
    Environment = "production"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.eligibai_vpc.id

  tags = {
    Name = "eligibai-igw"
    Environment = "production"
  }
}

# Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.eligibai_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "eligibai-public-rt"
    Environment = "production"
  }
}

# Route Table Associations
resource "aws_route_table_association" "public_rta_1" {
  subnet_id      = aws_subnet.public_subnet_1.id
  route_table_id = aws_route_table.public_rt.id
}

resource "aws_route_table_association" "public_rta_2" {
  subnet_id      = aws_subnet.public_subnet_2.id
  route_table_id = aws_route_table.public_rt.id
}

# Security Group
resource "aws_security_group" "web_sg" {
  name        = "eligibai-web-sg"
  description = "Security group for web servers"
  vpc_id      = aws_vpc.eligibai_vpc.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 3000
    to_port     = 3000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 8000
    to_port     = 8000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "eligibai-web-sg"
    Environment = "production"
  }
}

# RDS PostgreSQL
resource "aws_db_subnet_group" "private_subnet_group" {
  name       = "eligibai-db-subnet-group"
  subnet_ids = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]

  tags = {
    Name = "eligibai-db-subnet-group"
    Environment = "production"
  }
}

resource "aws_db_instance" "postgres" {
  allocated_storage      = 20
  storage_type           = "gp2"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t3.micro"
  db_name                = "eligibai"
  username               = "eligibai"
  password               = "eligibai_secure_password"
  db_subnet_group_name  = aws_db_subnet_group.private_subnet_group.name
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  skip_final_snapshot   = true
  publicly_accessible    = false

  tags = {
    Name = "eligibai-postgres"
    Environment = "production"
  }
}

# ElastiCache Redis
resource "aws_elasticache_subnet_group" "redis_subnet_group" {
  name        = "eligibai-redis-subnet-group"
  subnet_ids  = [aws_subnet.private_subnet_1.id, aws_subnet.private_subnet_2.id]

  tags = {
    Name = "eligibai-redis-subnet-group"
    Environment = "production"
  }
}

resource "aws_elasticache_replication_group" "redis" {
  replication_group_id          = "eligibai-redis"
  replication_group_description = "ElastiCache Redis for EligibAI"
  node_type                     = "cache.t3.micro"
  number_cache_clusters         = 1
  engine                        = "redis"
  engine_version                = "7.0"
  parameter_group_name          = "default.redis7"
  subnet_group_name             = aws_elasticache_subnet_group.redis_subnet_group.name
  security_group_ids            = [aws_security_group.web_sg.id]

  tags = {
    Name = "eligibai-redis"
    Environment = "production"
  }
}

# ECS Cluster
resource "aws_ecs_cluster" "eligibai_cluster" {
  name = "eligibai-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "eligibai-ecs-cluster"
    Environment = "production"
  }
}

# Application Load Balancer
resource "aws_lb" "eligibai_alb" {
  name               = "eligibai-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.web_sg.id]
  subnets           = [aws_subnet.public_subnet_1.id, aws_subnet.public_subnet_2.id]

  tags = {
    Name = "eligibai-alb"
    Environment = "production"
  }
}

resource "aws_lb_target_group" "frontend_tg" {
  name        = "eligibai-frontend-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.eligibai_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = 3000
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "eligibai-frontend-tg"
    Environment = "production"
  }
}

resource "aws_lb_target_group" "backend_tg" {
  name        = "eligibai-backend-tg"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.eligibai_vpc.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/health"
    port                = 8000
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "eligibai-backend-tg"
    Environment = "production"
  }
}

resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.eligibai_alb.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.frontend_tg.arn
  }
}

# Output values
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.eligibai_vpc.id
}

output "alb_dns" {
  description = "Load Balancer DNS"
  value       = aws_lb.eligibai_alb.dns_name
}

output "db_endpoint" {
  description = "Database endpoint"
  value       = aws_db_instance.postgres.endpoint
}

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = aws_elasticache_replication_group.redis.primary_endpoint_address
}