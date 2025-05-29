terraform {
  backend "s3" {
    bucket         = "lee-aws-devsecops"
    region         = "us-east-1"
    encrypt        = true
    use_lockfile   = true # Enables S3-native state locking
  }
}
