terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.0"
    }
  }
}

provider "aws" {
  region = "eu-central-1"  # Set your preferred region
}

variable "bucket_name" {
  description = "The name of the S3 bucket"
  type        = string
  default     = "my-unique-terraform-bucket875422154872456"
}

variable "lambda_runtime" {
  description = "The runtime for the Lambda functions"
  type        = string
  default     = "python3.8"
}

variable "lambda_handler" {
  description = "The handler for the Lambda functions"
  type        = string
  default     = "lambda_function.lambda_handler"
}

resource "aws_s3_bucket" "my_bucket" {
  bucket = var.bucket_name  # Ensure this is unique
  acl    = "private"  # Set the ACL directly here
}

data "archive_file" "get_and_save_data_in_db_zip" {
  type        = "zip"
  source_file = "getAndSaveIntoDynamodb.py"
  output_path = "getAndSaveIntoDynamodb.zip"
}

data "archive_file" "return_diff_exchange_rate_zip" {
  type        = "zip"
  source_file = "returnDiff.py"
  output_path = "returnDiff.zip"
}

resource "aws_s3_bucket_object" "saveLambdaObject" {
  bucket = aws_s3_bucket.my_bucket.bucket
  key    = "saveLambdaObject.zip"
  source = data.archive_file.get_and_save_data_in_db_zip.output_path
}

resource "aws_s3_bucket_object" "returnDiffExchangeRateObject" {
  bucket = aws_s3_bucket.my_bucket.bucket
  key    = "returnDiffExchangeRate.zip"
  source = data.archive_file.return_diff_exchange_rate_zip.output_path
}

resource "aws_dynamodb_table" "exchangeRates" {
  name           = "exchangeRates"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "Date"

  attribute {
    name = "Date"
    type = "S"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "lambda_role"

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

resource "aws_iam_role_policy_attachment" "lambda_basic_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_policy" "dynamodb_policy" {
  name        = "lambda_dynamodb_policy"
  description = "IAM policy for Lambda to access DynamoDB"
  policy      = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = [
          "dynamodb:PutItem",
          "dynamodb:UpdateItem",
          "dynamodb:GetItem",  # Added permission to read data
          "dynamodb:Query",     # Added permission to query data
          "dynamodb:Scan"
        ]
        Effect   = "Allow"
        Resource = aws_dynamodb_table.exchangeRates.arn  # Use the table ARN
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_dynamodb_policy_attachment" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = aws_iam_policy.dynamodb_policy.arn
}

resource "aws_lambda_function" "get_and_save_data_in_db" {
  function_name = "get_and_save_data_in_db"
  s3_bucket     = aws_s3_bucket.my_bucket.bucket
  s3_key        = aws_s3_bucket_object.saveLambdaObject.key
  handler       = "getAndSaveIntoDynamodb.lambda_handler"  # Update this to your handler
  runtime       = var.lambda_runtime  # Update this to your Python runtime
  role          = aws_iam_role.lambda_role.arn

  provisioner "local-exec" {
    command = "aws lambda invoke --function-name ${aws_lambda_function.get_and_save_data_in_db.function_name} output.txt"
    }
}

resource "aws_lambda_function" "return_diff_exchange_rate_lambda" {
  function_name = "return_diff_exchange_rate_lambda"
  s3_bucket     = aws_s3_bucket.my_bucket.bucket
  s3_key        = aws_s3_bucket_object.returnDiffExchangeRateObject.key
  handler       = "returnDiff.lambda_handler"  # Update this to your handler
  runtime       = var.lambda_runtime  # Update this to your Python runtime
  role          = aws_iam_role.lambda_role.arn
}

resource "aws_cloudwatch_event_rule" "lambda_schedule" {
  name                = "lambda-schedule"
  description         = "Trigger Lambda every day at 10 AM"
  schedule_expression = "cron(20 16 * * ? *)"
}

resource "aws_cloudwatch_event_target" "lambda_target" {
  rule      = aws_cloudwatch_event_rule.lambda_schedule.name
  target_id = "get_and_save_data_in_db"
  arn       = aws_lambda_function.get_and_save_data_in_db.arn
}

resource "aws_lambda_permission" "allow_cloudwatch" {
  statement_id  = "AllowExecutionFromCloudWatch"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.get_and_save_data_in_db.function_name
  principal     = "events.amazonaws.com"
  source_arn    = aws_cloudwatch_event_rule.lambda_schedule.arn
}

resource "aws_api_gateway_rest_api" "api" {
  name        = "returnDiffExchangeRateAPI"
  description = "API Gateway for returnDiffExchangeRate Lambda function"
}

resource "aws_api_gateway_resource" "api_resource" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  parent_id   = aws_api_gateway_rest_api.api.root_resource_id
  path_part   = "returnDiffExchangeRate"
}

resource "aws_api_gateway_method" "api_method" {
  rest_api_id   = aws_api_gateway_rest_api.api.id
  resource_id   = aws_api_gateway_resource.api_resource.id
  http_method   = "GET"
  authorization = "NONE"
}

resource "aws_api_gateway_integration" "api_integration" {
  rest_api_id = aws_api_gateway_rest_api.api.id
  resource_id = aws_api_gateway_resource.api_resource.id
  http_method = aws_api_gateway_method.api_method.http_method
  type        = "AWS_PROXY"
  integration_http_method = "POST"
  uri         = aws_lambda_function.return_diff_exchange_rate_lambda.invoke_arn
}

resource "aws_lambda_permission" "api_gateway_permission" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.return_diff_exchange_rate_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_api_gateway_rest_api.api.execution_arn}/*/*"
}

resource "aws_api_gateway_deployment" "api_deployment" {
  depends_on = [aws_api_gateway_integration.api_integration]
  rest_api_id = aws_api_gateway_rest_api.api.id
  stage_name  = "prod"
}

output "api_gateway_url" {
  description = "The URL of the API Gateway"
  value       = "${aws_api_gateway_deployment.api_deployment.invoke_url}/returnDiffExchangeRate"
}