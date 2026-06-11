# terraform/outputs.tf

output "cloudfront_domain_name" {
  value       = aws_cloudfront_distribution.frontend.domain_name
  description = "The URL to visit the React frontend application served by CloudFront (redirects to HTTPS)"
}

output "load_balancer_dns" {
  value       = aws_lb.main.dns_name
  description = "The DNS address of the Application Load Balancer routing backend API traffic"
}

output "ec2_public_ip" {
  value       = aws_instance.backend_server.public_ip
  description = "The Public IP of the backend EC2 server instance (use SSH with the configured key to connect)"
}
