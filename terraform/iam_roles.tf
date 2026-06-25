resource "aws_iam_role" "ec2_ecr_role" {
  name = "ec2-ecr-readonly-role"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"

      Principal = {
        Service = "ec2.amazonaws.com"
      }

      Action = "sts:AssumeRole"
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_readonly" {
  role       = aws_iam_role.ec2_ecr_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

resource "aws_iam_instance_profile" "ec2_profile" {
  name = "ec2-ecr-readonly-profile"
  role = aws_iam_role.ec2_ecr_role.name
}

resource "aws_iam_role" "ecr_full_access" {
  name = "github-actions-ecr-full-acsses"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"

    Statement = [{
      Effect = "Allow"

      Principal = {
        Federated = "arn:aws:iam::547320736290:oidc-provider/token.actions.githubusercontent.com"
      }

      Action = "sts:AssumeRoleWithWebIdentity"

      Condition = {
        StringEquals = {
          "token.actions.githubusercontent.com:aud" = "sts.amazonaws.com"
        }

        StringLike = {
          "token.actions.githubusercontent.com:sub" = "repo:Carneiro1908/DevOpsProject-Website:*"
        }
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr_full_access" {
  role       = aws_iam_role.ecr_full_access.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryFullAccess"
}