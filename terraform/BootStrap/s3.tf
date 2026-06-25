resource "aws_s3_bucket" "backend_bucket_s3" {
  bucket = "terraform-state-tomaslima"

}


resource "aws_s3_bucket_public_access_block" "BlockBucketPublicAcsses" {
  bucket = aws_s3_bucket.backend_bucket_s3.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_ownership_controls" "BucketOwnership" {
  bucket = aws_s3_bucket.backend_bucket_s3.id

  rule {
    object_ownership = "BucketOwnerEnforced"
  }
}