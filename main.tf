provider "aws" {
  region = "us-east-1"
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_policy" {
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
  role = aws_iam_role.lambda_role.name
}

resource "aws_iam_role_policy_attachment" "secrets_manager_policy" {
  policy_arn = "arn:aws:iam::aws:policy/SecretsManagerReadWrite"
  role       = aws_iam_role.lambda_role.name
}

resource "aws_lambda_function" "flowtrack-aggregator" {
  filename = "flowtrack-aggregator.zip"
  function_name = "flowtrack_data_aggregator"
  role = aws_iam_role.lambda_role.arn
  handler = "lambda_function.lambda_handler"
  runtime = "python3.12"

  source_code_hash = filebase64sha256("flowtrack-aggregator.zip")
  
  environment {
    variables = {
      DB_HOST = "flowtrack-db-devel.ctskaiq8mthm.us-east-1.rds.amazonaws.com"
      DB_PORT = 5432    
    }
  }

  timeout = 60
}


