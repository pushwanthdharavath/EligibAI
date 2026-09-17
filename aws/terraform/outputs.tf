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