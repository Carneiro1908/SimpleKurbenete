terraform {
  backend "s3" {
    bucket       = "terraform-state-tomaslima"
    key          = "site/terraform.tfstate"
    region       = "eu-north-1"
    encrypt      = true
    use_lockfile = true
  }
}