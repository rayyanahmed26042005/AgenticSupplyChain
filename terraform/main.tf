# terraform/main.tf

terraform {
  required_version = ">= 1.3.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
}

# ================= 1. NETWORK (VPC Setup) =================

resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  tags = {
    Name        = "supply-chain-vpc"
    Environment = "production"
  }
}

resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "supply-chain-igw" }
}

# Public Subnets (For ALB and public EC2)
resource "aws_subnet" "public_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = "${var.aws_region}a"
  map_public_ip_on_launch = true
  tags = { Name = "supply-chain-public-subnet-a" }
}

resource "aws_subnet" "public_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = "${var.aws_region}b"
  map_public_ip_on_launch = true
  tags = { Name = "supply-chain-public-subnet-b" }
}

# Private Subnets (For RDS Database)
resource "aws_subnet" "private_a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.3.0/24"
  availability_zone = "${var.aws_region}a"
  tags = { Name = "supply-chain-private-subnet-a" }
}

resource "aws_subnet" "private_b" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.4.0/24"
  availability_zone = "${var.aws_region}b"
  tags = { Name = "supply-chain-private-subnet-b" }
}

# Routing
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  tags = { Name = "supply-chain-public-rt" }
}

resource "aws_route_table_association" "pub_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "pub_b" {
  subnet_id      = aws_subnet.public_b.id
  route_table_id = aws_route_table.public.id
}

# ================= 2. SECURITY GROUPS =================

# Application Load Balancer SG (Public HTTP access)
resource "aws_security_group" "alb" {
  name        = "supply-chain-alb-sg"
  description = "Allow public HTTP traffic to Load Balancer"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# EC2 Instance SG (Only traffic from Load Balancer, and optional SSH)
resource "aws_security_group" "ec2" {
  name        = "supply-chain-ec2-sg"
  description = "Allow backend traffic from ALB and SSH"
  vpc_id      = aws_vpc.main.id

  # Backend port (only accessible via ALB)
  ingress {
    from_port       = 8000
    to_port         = 8000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }

  # SSH Access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] # In production, lock this down to your public IP!
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS Security Group
resource "aws_security_group" "db" {
  name        = "supply-chain-db-sg"
  description = "Allow Postgres access from EC2 instance"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ec2.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ================= 3. DATABASES & PERSISTENCE =================

# Managed PostgreSQL Group
resource "aws_db_subnet_group" "db" {
  name       = "supply-chain-db-subnet-group"
  subnet_ids = [aws_subnet.private_a.id, aws_subnet.private_b.id]
}

resource "aws_db_instance" "postgres" {
  identifier             = "supply-chain-db"
  allocated_storage      = 20
  max_allocated_storage  = 100
  storage_type           = "gp3"
  engine                 = "postgres"
  engine_version         = "15.4"
  instance_class         = "db.t4g.micro" # Free Tier eligible instance type
  db_name                = "supply_chain"
  username               = "postgres"
  password               = var.db_password
  db_subnet_group_name   = aws_db_subnet_group.db.name
  vpc_security_group_ids = [aws_security_group.db.id]
  skip_final_snapshot    = true
  publicly_accessible    = false
}

# DynamoDB Table (For operational tracking or logs)
resource "aws_dynamodb_table" "events" {
  name           = "supply-chain-events"
  billing_mode   = "PAY_PER_REQUEST" # Serverless cost-saving billing
  hash_key       = "event_id"

  attribute {
    name = "event_id"
    type = "S"
  }

  tags = {
    Name        = "supply-chain-events-table"
    Environment = "production"
  }
}

# ================= 4. EC2 BACKEND SERVER =================

# IAM Role for EC2 (To write logs to CloudWatch and download images from ECR if used)
resource "aws_iam_role" "ec2_role" {
  name = "supply-chain-ec2-execution-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action    = "sts:AssumeRole"
      Effect    = "Allow"
      Principal = { Service = "ec2.amazonaws.com" }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "cw_logs" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "supply-chain-ec2-profile"
  role = aws_iam_role.ec2_role.name
}

# EC2 Instance Key Pair (Provide name via variables)
resource "aws_key_pair" "deployer" {
  key_name   = "supply-chain-key"
  public_key = var.ssh_public_key
}

# EC2 Instance
resource "aws_instance" "backend_server" {
  ami                  = var.ubuntu_ami_id
  instance_type        = "t2.micro" # Free-Tier eligible instance
  subnet_id            = aws_subnet.public_a.id
  vpc_security_group_ids = [aws_security_group.ec2.id]
  key_name             = aws_key_pair.deployer.key_name
  instance_profile     = aws_iam_instance_profile.ec2_profile.name

  # Bootstraps Docker & runs Backend container automatically
  user_data = <<-EOF
              #!/bin/bash
              apt-get update -y
              apt-get install -y docker.io docker-compose
              systemctl start docker
              systemctl enable docker
              usermod -aG docker ubuntu

              # Create application directories
              mkdir -p /app/data /app/logs

              # Write env variables to file
              cat <<EOT > /app/.env
              ENVIRONMENT=production
              APP_MODE=simulation
              DATA_SOURCE=manual
              DATABASE_URL=postgresql+asyncpg://postgres:${var.db_password}@${aws_db_instance.postgres.endpoint}/supply_chain
              MONGODB_URI=${var.mongodb_uri}
              GROQ_API_KEY=${var.groq_api_key}
              GROQ_MODEL=llama-3.3-70b-versatile
              USE_LLM_AGENTS=true
              EOT

              # Pull and run the backend image
              # (CI/CD pipeline updates this container on release)
              docker run -d --name backend \
                --restart always \
                -p 8000:8000 \
                --env-file /app/.env \
                -v /app/data:/app/data \
                -v /app/logs:/app/logs \
                python:3.13-slim tail -f /dev/null
              EOF

  tags = {
    Name        = "supply-chain-backend-server"
    Environment = "production"
  }
}

# ================= 5. LOAD BALANCER (ALB) =================

resource "aws_lb" "main" {
  name               = "supply-chain-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = [aws_subnet.public_a.id, aws_subnet.public_b.id]
}

resource "aws_lb_target_group" "backend" {
  name        = "tg-backend"
  port        = 8000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "instance"

  health_check {
    path                = "/api/v1/data/status"
    port                = "8000"
    protocol            = "HTTP"
    healthy_threshold   = 3
    unhealthy_threshold = 3
    timeout             = 5
    interval            = 30
  }
}

resource "aws_lb_target_group_attachment" "backend" {
  target_group_arn = aws_lb_target_group.backend.arn
  target_id        = aws_instance.backend_server.id
  port             = 8000
}

# Router Listener mapping requests to ALB
resource "aws_lb_listener" "http" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.backend.arn
  }
}

# ================= 6. FRONTEND (S3 & CloudFront) =================

# S3 Bucket for Static Assets
resource "aws_s3_bucket" "frontend" {
  bucket        = var.s3_bucket_name
  force_destroy = true
}

resource "aws_s3_bucket_public_access_block" "frontend" {
  bucket = aws_s3_bucket.frontend.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# CloudFront Origin Access Control (OAC) to read S3 bucket
resource "aws_cloudfront_origin_access_control" "oac" {
  name                              = "s3-frontend-oac"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution
resource "aws_cloudfront_distribution" "frontend" {
  origin {
    domain_name              = aws_s3_bucket.frontend.bucket_regional_domain_name
    origin_id                = "S3-Frontend"
    origin_access_control_id = aws_cloudfront_origin_access_control.oac.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-Frontend"

    forwarded_values {
      query_string = false
      cookies { forward = "none" }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600
    max_ttl                = 86400
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Fallback rule for React Single Page App routing
  custom_error_response {
    error_code            = 403
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }
  
  custom_error_response {
    error_code            = 404
    response_code         = 200
    response_page_path    = "/index.html"
    error_caching_min_ttl = 10
  }

  tags = {
    Name        = "supply-chain-frontend-distribution"
    Environment = "production"
  }
}

# S3 Bucket policy allowing CloudFront access
resource "aws_s3_bucket_policy" "cloudfront_access" {
  bucket = aws_s3_bucket.frontend.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "AllowCloudFrontServicePrincipalReadOnly"
        Effect    = "Allow"
        Principal = { Service = "cloudfront.amazonaws.com" }
        Action    = "s3:GetObject"
        Resource  = "${aws_s3_bucket.frontend.arn}/*"
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.frontend.arn
          }
        }
      }
    ]
  })
}

# ================= 7. MONITORING =================

resource "aws_cloudwatch_log_group" "backend" {
  name              = "/aws/ec2/supply-chain-backend"
  retention_in_days = 7
}
