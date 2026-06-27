terraform {
  required_version = ">= 1.5.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1" # Altere para a região de sua preferência
}

# 1. Criação da VPC estruturada para o EKS
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  name = "k8s-vpc-comunidade"
  cidr = "10.0.0.0/16"

  azs             = ["us-east-1a", "us-east-1b"]
  private_subnets = ["10.0.1.0/24", "10.0.2.0/24"]
  public_subnets  = ["10.0.101.0/24", "10.0.102.0/24"]

  enable_nat_gateway = true
  single_nat_gateway = true # Economiza custos em ambientes de teste

  # Tags obrigatórias para que o Kubernetes crie Load Balancers automaticamente
  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }

  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }
}

# 2. Criação do Cluster EKS e Node Groups
module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 20.0"

  cluster_name    = "meu-cluster-k8s"
  cluster_version = "1.33" # Versão estável do Kubernetes

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets # Nós rodam em subnets privadas por segurança

  # Garante que o criador do cluster (você) tenha permissão de Admin no k8s automaticamente
  enable_cluster_creator_admin_permissions = true

  cluster_endpoint_public_access = true

  # Configuração dos Worker Nodes (Máquinas onde rodam os pods)
  eks_managed_node_groups = {
    grupo_principal = {
      min_size     = 1
      max_size     = 3
      desired_size = 2

      instance_types = ["t3.micro"] 
      capacity_type  = "ON_DEMAND"   # Use "SPOT" se quiser economizar até 70%
    }
  }
}

# Output para facilitar a conexão posterior
output "cluster_name" {
  value = module.eks.cluster_name
}