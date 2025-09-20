#!/bin/bash

# 1. Create RDS PostgreSQL instance with pgvector
aws rds create-db-instance \
  --db-instance-identifier documentgpt-db \
  --db-instance-class db.t3.micro \
  --engine postgres \
  --engine-version 17.6 \
  --master-username postgres \
  --master-user-password $(openssl rand -base64 12) \
  --allocated-storage 20 \
  --vpc-security-group-ids $(aws ec2 describe-security-groups --group-names default --query 'SecurityGroups[0].GroupId' --output text) \
  --publicly-accessible \
  --storage-encrypted

echo "RDS instance creating... This takes 5-10 minutes"
echo "Next: Run setup-vectors.sql on the database"