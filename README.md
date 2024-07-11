# Terraform AWS Infrastructure Setup with Unit Test Coverage

This project sets up an AWS infrastructure using Terraform. It includes the following resources:
- S3 bucket to store Lambda function code
- DynamoDB table to store exchange rates
- Lambda functions to process and return exchange rates
- CloudWatch Events to trigger Lambda functions on a schedule
- API Gateway to expose a public API for the Lambda function

## Prerequisites

- Python 3.x installed
- Pip installed
- [Terraform](https://www.terraform.io/downloads.html) installed
- AWS CLI configured with appropriate credentials
- An AWS account

## Setup Instructions

### 1. Clone the Repository

```sh
git clone https://github.com/sajidrai/CCLPythonTask.git
cd CCLPythonTask
```
### 2. Install Python Dependencies
Install the necessary Python packages for running unit tests.
```sh
pip install -r requirements.txt
```
### 3. Running Unit Tests for Coverage
Run unit tests for coverage by executing the following command:
```sh
python3 run_coverage.py
```
### 4. Initialize Terraform
Initialize the Terraform working directory, which will download the necessary provider plugins.

```sh
terraform init
```
### 5. Review the Terraform Plan
Review the Terraform plan to see what resources will be created.
```sh
terraform plan
```
### 6. Apply the Terraform Plan
Apply the Terraform plan to create the resources.
```sh
terraform apply 
```
Type yes when prompted to confirm the apply.
After successful deployment api gateway public link will be displayed at the end use that to test the API.

wait for 5, 10 seconds so that dynamodb table created and data is populated.

Outputs:
api_gateway_url = "<API_TESTING_URL>"

better to test the application after 16:00 CET as the reference rates are usually updated at around 16:00 CET every working day, except on TARGET closing days. [Learn more about CET time zone](https://en.wikipedia.org/wiki/Central_European_Time)

### 7. Verify the Deployment
After the Terraform apply completes, you can verify the deployment by checking the AWS Management Console for the created resources:

S3 bucket
DynamoDB table
Lambda functions
CloudWatch Events rule
API Gateway
