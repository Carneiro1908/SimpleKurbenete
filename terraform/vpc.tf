resource "aws_vpc" "devops_project_vpc" {
  cidr_block = "10.0.0.0/16"

  tags = {
    Name = "devops-project-vpc"
  }
}

resource "aws_subnet" "public" {
  vpc_id                  = aws_vpc.devops_project_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "eu-north-1a"
  map_public_ip_on_launch = true

  tags = {
    Name = "public-subnet"
  }
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.devops_project_vpc.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.igw.id
  }

  tags = {
    Name = "public-route-table"
  }
}

resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.devops_project_vpc.id

  tags = {
    Name = "devops-project-igw"
  }
}

resource "aws_route_table_association" "public" {
  subnet_id      = aws_subnet.public.id
  route_table_id = aws_route_table.public.id
}