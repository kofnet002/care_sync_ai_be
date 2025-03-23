#!/bin/bash

# ECR repository information
ECR_URI="529088270123.dkr.ecr.us-east-1.amazonaws.com"
ECR_REPO="caresyncai-repo"

# Local repository names
LOCAL_REPOS=(
  "caresyncai-celery_worker"
  "caresyncai-web"
  "caresyncai-db"
  "caresyncai-redis"
  "caresyncai-nginx"
)

# Get ECR authentication token and save to a file
echo "Getting ECR authentication token..."
ECR_TOKEN=$(aws ecr get-login-password --region us-east-1)
if [ $? -ne 0 ]; then
  echo "Failed to get ECR authentication token. Check your AWS credentials."
  exit 1
fi

# Login to ECR with sudo
echo "Logging in to Amazon ECR..."
echo $ECR_TOKEN | sudo docker login --username AWS --password-stdin $ECR_URI
if [ $? -ne 0 ]; then
  echo "Failed to log in to ECR."
  exit 1
fi

# Tag and push each local repository
for repo in "${LOCAL_REPOS[@]}"; do
  echo "Processing $repo..."
  
  # Check if the local image exists
  if ! sudo docker image inspect $repo:latest &>/dev/null; then
    echo "Warning: Image $repo:latest does not exist locally. Skipping."
    echo "------------------------------"
    continue
  fi
  
  # Tag with repo name as the tag
  echo "Tagging $repo:latest as $ECR_URI/$ECR_REPO:$repo"
  sudo docker tag $repo:latest $ECR_URI/$ECR_REPO:$repo
  
  # Push to ECR
  echo "Pushing $ECR_URI/$ECR_REPO:$repo to ECR..."
  sudo docker push $ECR_URI/$ECR_REPO:$repo
  
  if [ $? -eq 0 ]; then
    echo "$repo successfully pushed to ECR"
  else
    echo "Failed to push $repo to ECR"
  fi
  echo "------------------------------"
done

echo "All repositories have been tagged and pushed to ECR"