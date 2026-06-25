resource "aws_key_pair" "ec2_key" {
  key_name   = "EC2-Key-terraform"
  public_key = file("${path.module}/../.github/workflows/sshkey/EC2KeyDevOpsProject16062026.pub")
}

resource "aws_instance" "website_server" {
  ami           = "ami-00263659a97a6c29c" # ID to select amazon linux as OS  
  instance_type = "t3.micro"

  key_name = aws_key_pair.ec2_key.key_name

  subnet_id = aws_subnet.public.id

  vpc_security_group_ids = [aws_security_group.website_sg.id]

  iam_instance_profile = aws_iam_instance_profile.ec2_profile.name

  user_data = file("../bash/user_data.sh")

  tags = {
    Name        = "website-server"
    Provisioned = "terraform"
    Client      = "Tomas"
  }
}

resource "aws_security_group" "website_sg" {
  name        = "website-sg"
  description = "Security group for website"
  vpc_id      = aws_vpc.devops_project_vpc.id

  tags = {
    Name        = "website-sg"
    Provisioned = "terraform"
    Client      = "Tomas"
  }
}


# Network configurations

# Ingress rules 
resource "aws_vpc_security_group_ingress_rule" "allow_ssh" {
  security_group_id = aws_security_group.website_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 22
  ip_protocol       = "tcp"
  to_port           = 22
}

resource "aws_vpc_security_group_ingress_rule" "allow_http" {
  security_group_id = aws_security_group.website_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 80
  ip_protocol       = "tcp"
  to_port           = 80
}
resource "aws_vpc_security_group_ingress_rule" "allow_https" {
  security_group_id = aws_security_group.website_sg.id
  cidr_ipv4         = "0.0.0.0/0"
  from_port         = 443
  ip_protocol       = "tcp"
  to_port           = 443
}

# Egress rules (to upload the container on the EC2)
resource "aws_vpc_security_group_egress_rule" "allow_all_outbound" {
  security_group_id = aws_security_group.website_sg.id

  cidr_ipv4   = "0.0.0.0/0"
  ip_protocol = -1
}