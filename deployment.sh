# #!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Function to execute on exit
function on_exit {
    exit_code=$?
    if [ $exit_code -ne 0 ]; then
        echo "-------------------------"
        echo "An error occurred during the deployment."
        echo "Please check the error messages above."
        echo "-------------------------"
    else
        echo "-------------------------"
        echo "Deployment completed successfully."
        echo "-------------------------"
    fi
    # Wait for user input before closing
    read -rn1 -p "Press any key to exit..."
}

# Trap the EXIT signal to call on_exit function
trap on_exit EXIT

echo "-------------------------"
echo "Build Images"
echo "-------------------------"

#Variables
BACKEND_TAG="beatblend-server"
FRONTEND_TAG="beatblend-client"

SPOTIFY_CLIENT_ID="d3d3c0137d7942c893be8c1157ed65fb"
SPOTIFY_REDIRECT_URI="https://beatblend.ch/spotify-callback"
API_BASE_URL="https://api.beatblend.ch"
WS_BASE_URL="wss://api.beatblend.ch"

# Build Backend & Frontend Images
echo "Building backend Docker image..."
docker build -t $BACKEND_TAG:latest -f ./server/Dockerfile.prod ./server

echo "Building frontend Docker image..."
docker build \
  --build-arg VITE_SPOTIFY_CLIENT_ID=$SPOTIFY_CLIENT_ID \
  --build-arg VITE_SPOTIFY_REDIRECT_URI=$SPOTIFY_REDIRECT_URI \
  --build-arg VITE_API_BASE_URL=$API_BASE_URL \
  --build-arg VITE_WS_BASE_URL=$WS_BASE_URL \
  -t $FRONTEND_TAG:latest -f ./client/Dockerfile.prod ./client

echo "Docker images built successfully."

echo "-------------------------"
echo "Push Images to ECR"
echo "-------------------------"

# Variables
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION="eu-central-2"
ECR_REGISTRY="$AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
BACKEND_REPO_NAME="beatblend-server"
FRONTEND_REPO_NAME="beatblend-client"

# Authenticate Docker to ECR
echo "Authenticating Docker to ECR..."
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin "$ECR_REGISTRY"

# Tag and Push Backend Image
echo "Tagging and pushing backend image..."
docker tag $BACKEND_TAG:latest "$ECR_REGISTRY"/$BACKEND_REPO_NAME:latest
docker push "$ECR_REGISTRY"/$BACKEND_REPO_NAME:latest

# Tag and Push Frontend Image
echo "Tagging and pushing frontend image..."
docker tag $FRONTEND_TAG:latest "$ECR_REGISTRY"/$FRONTEND_REPO_NAME:latest
docker push "$ECR_REGISTRY"/$FRONTEND_REPO_NAME:latest

echo "Docker images pushed to ECR successfully."

echo "-------------------------"
echo "Deploy Infrastructure"
echo "-------------------------"

# Variables
STACK_NAME="InfraStack"
CDK_DIRECTORY="infra"

cd $CDK_DIRECTORY || { echo "Failed to change directory to $CDK_DIRECTORY"; exit 1; }

# Bootstrap the environment
echo "Bootstrapping the CDK environment..."
cdk bootstrap aws://"$AWS_ACCOUNT_ID"/$AWS_REGION

# Synthesize CloudFormation Template
echo "Synthesizing CloudFormation template..."
cdk synth

# Deploy the Stack
echo "Deploying the CDK stack..."
cdk deploy $STACK_NAME --require-approval never

echo "CDK stack deployed successfully."