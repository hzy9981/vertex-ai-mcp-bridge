#!/bin/bash

# 配置变量
PROJECT_ID=$(gcloud config get-value project)
LOCATION="us-central1"
REPO_NAME="mcp-repo"
IMAGE_NAME="vertex-mcp-bridge"
SERVICE_NAME="vertex-mcp-service"
IMAGE_URL="$LOCATION-docker.pkg.dev/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME"

echo "开始部署 $SERVICE_NAME 到 Cloud Run..."

# 1. 创建 Artifact Registry 仓库
echo "创建 Artifact Registry 仓库..."
gcloud artifacts repositories create $REPO_NAME 
    --repository-format=docker 
    --location=$LOCATION 
    --description="MCP Repository" 
    --quiet || echo "仓库已存在，跳过创建。"

# 2. 构建并推送镜像
echo "构建并推送镜像到 Artifact Registry..."
gcloud builds submit --tag $IMAGE_URL --quiet

# 3. 部署到 Cloud Run
echo "部署到 Cloud Run..."
gcloud run deploy $SERVICE_NAME 
    --image $IMAGE_URL 
    --platform managed 
    --region $LOCATION 
    --allow-unauthenticated 
    --set-env-vars GOOGLE_CLOUD_PROJECT=$PROJECT_ID,PORT=8080 
    --quiet

echo "部署完成！"
echo "您的服务 URL 是: $(gcloud run services describe $SERVICE_NAME --region $LOCATION --format 'value(status.url)')"
