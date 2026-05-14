#!/bin/bash
set -e

# 获取当前项目 ID
PROJECT_ID=$(gcloud config get-value project 2>/dev/null)
if [ -z "$PROJECT_ID" ]; then
    PROJECT_ID=$GOOGLE_CLOUD_PROJECT
fi

if [ -z "$PROJECT_ID" ]; then
    echo "错误: 未能获取到 Google Cloud 项目 ID。请确保已运行 'gcloud auth login' 并设置了项目，或者设置了 GOOGLE_CLOUD_PROJECT 环境变量。"
    exit 1
fi

REGION="us-central1"
SERVICE_NAME="vertex-mcp-server"

echo "--- 正在构建镜像并部署到 Cloud Run (使用 --source) ---"
gcloud run deploy "$SERVICE_NAME" \
    --project "$PROJECT_ID" \
    --source . \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --memory=1Gi \
    --set-env-vars GOOGLE_CLOUD_PROJECT="$PROJECT_ID",GOOGLE_CLOUD_LOCATION="$REGION",DASHSCOPE_API_KEY="$DASHSCOPE_API_KEY"

echo "--- 部署完成！ ---"
SERVICE_URL=$(gcloud run services describe "$SERVICE_NAME" --project "$PROJECT_ID" --platform managed --region "$REGION" --format 'value(status.url)')
echo "服务 URL: $SERVICE_URL"
echo "您现在可以使用该 URL 作为您的 MCP SSE 端点。"
