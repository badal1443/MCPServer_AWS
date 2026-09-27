# MCP Server on AWS Lambda

A Model Context Protocol (MCP) server deployed on AWS Lambda. This project provides a serverless endpoint that can be accessed by MCP-compatible clients and applications.

## 1. Purpose

This project implements an MCP server using Python and deploys it as a container image to AWS Lambda.

The server is designed to:

- Expose MCP tools and resources to compatible clients.
- Run server-side logic in a serverless AWS environment.
- Scale automatically through AWS Lambda.
- Use Amazon Elastic Container Registry (Amazon ECR) to store the deployment image.
- Automate building, and deployment through Bitbucket Pipelines.

## 2. Main Files

The main files in this project are:

| File | Description |
|------|-------------|
| `<mcp_server_file>.py` | Contains the MCP server implementation. |
| `<lambda_handler_file>.py` | Contains the AWS Lambda handler or application entry point. |
| `Dockerfile` | Defines the container image used to package the application for AWS Lambda. |
| `requirements.txt` | Contains the Python dependencies required by the application. |
| `bitbucket-pipelines.yaml` | Defines the CI/CD process for building, and deploying the application. |
| `.env` | Contains local environment variables. This file must not be committed to the repository. |

Update the table above with the actual filenames used in the project.

## 3. Configuration Required

### Local Configuration

Create a `.env` file in the project root if the application requires environment variables:

```env
AWS_REGION=<aws-region>
AWS_ACCOUNT_ID=<aws-account-id>
ECR_REPOSITORY_NAME=<ecr-repository-name>
LAMBDA_FUNCTION_NAME=<lambda-function-name>
LOG_LEVEL=INFO
```

Add any application-specific configuration required by the MCP server.

Do not commit secrets, access keys, tokens, passwords, or private configuration files to the repository.

### AWS Resources

The deployment requires the following AWS resources:

1. An Amazon ECR repository.
2. An AWS Lambda function configured to use the container image.
3. An IAM execution role for the Lambda function.
4. An API Gateway or Lambda Function URL if the server must be accessed over HTTP.
5. CloudWatch Logs for monitoring and troubleshooting.

### AWS Permissions

The AWS user or role used by Bitbucket Pipelines requires permission to:

- Authenticate with Amazon ECR.
- Build and push images to Amazon ECR.
- Update the Lambda function image.
- Read Lambda and deployment information.
- Access CloudWatch logs if log retrieval is required.

Use the minimum permissions necessary for your deployment.

### Bitbucket Repository Variables

Configure the following secured variables in Bitbucket:

| Variable | Description |
|----------|-------------|
| `AWS_ACCESS_KEY_ID` | AWS access key used by the pipeline. |
| `AWS_SECRET_ACCESS_KEY` | AWS secret key used by the pipeline. |
| `AWS_DEFAULT_REGION` | AWS region where the resources are deployed. |
| `AWS_ACCOUNT_ID` | AWS account ID. |
| `ECR_REPOSITORY_NAME` | Name of the Amazon ECR repository. |
| `LAMBDA_FUNCTION_NAME` | Name of the AWS Lambda function. |

If your pipeline uses different variable names, update this documentation accordingly.

## 4. How to Run Locally

### Prerequisites

Install the following tools:

- Python 3.9 or later
- `pip`
- Docker
- AWS CLI, if AWS services are required locally
- Git

### Clone the Repository

```bash
git clone https://github.com/badal1443/MCPServer_AWS.git
cd MCPServer_AWS
```

### Create a Virtual Environment

Linux and macOS:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
```

### Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Configure Environment Variables

Create a local `.env` file and add the required configuration:

```bash
cp .env.example .env
```

If the project does not contain an `.env.example` file, create `.env` manually using the variables described in the [Configuration Required](#3-configuration-required) section.

### Start the Application

Run the project using its Python entry point:

```bash
python <entry-point-file>.py
```

Replace `<entry-point-file>.py` with the actual application entry point.

If the project uses a different command, use the command defined by the project.

### Run with Docker

Build the image:

```bash
docker build -t mcp-server-aws:local .
```

Run the container:

```bash
docker run --rm \
  --env-file .env \
  -p 8080:8080 \
  mcp-server-aws:local
```

The port may need to be changed depending on the port configured by the application and Dockerfile.

## 5. Build and Deploy Using Bitbucket Pipelines

The deployment process is defined in `bitbucket-pipelines.yaml`.

The pipeline generally performs the following steps:

1. Install dependencies.
3. Build the Docker image.
4. Authenticate with Amazon ECR.
5. Push the image to Amazon ECR.
6. Update the AWS Lambda function to use the new image.

### Typical Deployment Flow

Push changes to the deployment branch:

```bash
git add .
git commit -m "Update MCP server"
git push origin main
```

Bitbucket Pipelines then starts automatically for the configured branch.

### Example Pipeline Commands

The exact pipeline depends on the current `bitbucket-pipelines.yaml`. A typical container-image deployment includes commands similar to the following:

```bash
# Build the Docker image
docker build -t ${ECR_REPOSITORY_NAME}:${BITBUCKET_COMMIT} .

# Authenticate with Amazon ECR
aws ecr get-login-password --region ${AWS_DEFAULT_REGION} | \
  docker login \
  --username AWS \
  --password-stdin ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com

# Tag the image
docker tag \
  ${ECR_REPOSITORY_NAME}:${BITBUCKET_COMMIT} \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${BITBUCKET_COMMIT}

# Push the image to ECR
docker push \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${BITBUCKET_COMMIT}

# Update Lambda to use the new image
aws lambda update-function-code \
  --function-name ${LAMBDA_FUNCTION_NAME} \
  --image-uri ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_DEFAULT_REGION}.amazonaws.com/${ECR_REPOSITORY_NAME}:${BITBUCKET_COMMIT}
```

Use the actual commands from `bitbucket-pipelines.yaml` as the authoritative deployment instructions.

### Pipeline Requirements

Before running the pipeline, confirm that:

- Bitbucket Pipelines is enabled.
- Docker services are enabled if Docker builds are performed.
- AWS credentials are configured as secured repository variables.
- The ECR repository already exists.
- The Lambda function already exists and is configured for container-image deployment.
- The pipeline branch matches the branch used for deployment.
- The Bitbucket deployment role has the required AWS permissions.

### Monitoring the Deployment

Pipeline status can be monitored from the **Pipelines** section of the Bitbucket repository.

AWS Lambda logs can be viewed with:

```bash
aws logs tail /aws/lambda/<lambda-function-name> \
  --follow \
  --region <aws-region>
```

## 6. How to Access

The MCP server can be accessed using the AWS integration configured for the Lambda function.

### Option 1: Lambda Function URL

If a Lambda Function URL is configured, access the server using:

```text
https://<lambda-function-url>
```

Example health-check request:

```bash
curl https://<lambda-function-url>/health
```

Replace the URL and path with the endpoint implemented by the application.

### Option 2: Amazon API Gateway

If Amazon API Gateway is configured, use the API Gateway URL:

```text
https://<api-id>.execute-api.<aws-region>.amazonaws.com/<stage>
```

Example request:

```bash
curl -X POST \
  https://<api-id>.execute-api.<aws-region>.amazonaws.com/<stage> \
  -H "Content-Type: application/json" \
  -d '<request-payload>'
```

Replace `<request-payload>` with the request format expected by the MCP server.

### Option 3: Direct Lambda Invocation

The Lambda function can also be invoked directly using the AWS CLI:

```bash
aws lambda invoke \
  --function-name <lambda-function-name> \
  --region <aws-region> \
  --payload '<json-payload>' \
  response.json
```

View the response:

```bash
cat response.json
```

### MCP Client Configuration

Configure your MCP-compatible client with the deployed endpoint.

The exact configuration depends on the client. A generic HTTP-based configuration may look like:

```json
{
  "mcpServers": {
    "aws-mcp-server": {
      "url": "https://<lambda-function-url-or-api-gateway-url>"
    }
  }
}
```

Replace the URL with the actual deployed endpoint and use the configuration format required by your MCP client.

## Troubleshooting

### Check Lambda Logs

```bash
aws logs tail /aws/lambda/<lambda-function-name> \
  --follow \
  --region <aws-region>
```

### Check the Lambda Image

```bash
aws lambda get-function \
  --function-name <lambda-function-name> \
  --region <aws-region>
```

### Check the ECR Repository

```bash
aws ecr describe-images \
  --repository-name <ecr-repository-name> \
  --region <aws-region>
```

### Common Problems

- **Access denied:** Check AWS IAM permissions and Bitbucket variables.
- **Image not found:** Confirm that the image was pushed to the correct ECR repository and region.
- **Lambda deployment failed:** Confirm that the Lambda function and ECR image use the same AWS region.
- **Request timeout:** Check Lambda timeout, memory, networking, and downstream service configuration.
- **Missing environment variables:** Confirm that required variables are configured in the Lambda function settings.
- **MCP client cannot connect:** Verify the API Gateway or Lambda Function URL, authentication, routes, and request format.

## Security Notes

- Never commit AWS access keys or secrets.
- Store sensitive values in Bitbucket secured variables or AWS Secrets Manager.
- Use IAM roles with least-privilege permissions.
- Enable authentication and authorization for public endpoints.
- Restrict access to the Lambda Function URL or API Gateway where appropriate.
- Review CloudWatch logs to ensure sensitive data is not written to logs.

## License

Add the project license information here.

## Maintainer

Maintained by [badal1443](https://github.com/badal1443).
