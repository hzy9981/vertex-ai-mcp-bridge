# 🚀 Deploying Vertex AI Bridge to Google Cloud Run

This guide will walk you through deploying the **Vertex AI Bridge MCP Server** as a serverless service on Google Cloud Run. 

## Why Cloud Run?
- **Zero Infrastructure**: No servers to manage. Scaling is handled automatically.
- **Cost Efficient**: Pay-per-use. Scales to zero when not in use.
- **SSE Support**: Native support for Server-Sent Events (SSE), the preferred transport for remote MCP servers.
- **Secure**: Integrated with Google Cloud IAM for robust authentication.

---

## 📋 Prerequisites

1. **Google Cloud Project**: An active GCP project with billing enabled.
2. **Google Cloud SDK**: Installed and authenticated (`gcloud auth login`).
3. **APIs Enabled**:
   ```bash
   gcloud services enable run.googleapis.com \
                          aiplatform.googleapis.com \
                          artifactregistry.googleapis.com \
                          cloudbuild.googleapis.com
   ```

---

## 🛠 Step 1: Prepare the Container

Ensure your `Dockerfile` is present in the root directory. Here is a recommended production-ready `Dockerfile`:

```dockerfile
FROM node:20-slim AS builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

FROM node:20-slim
WORKDIR /app
COPY --from=builder /app/dist ./dist
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json

ENV PORT=8080
EXPOSE 8080
CMD ["node", "dist/index.js"]
```

---

## 🔐 Step 2: Setup IAM & Security

Never use your personal account to run services. Create a dedicated Service Account with **Least Privilege**:

```bash
# 1. Create a service account
gcloud iam service-accounts create vertex-mcp-sa \
    --display-name="Vertex AI Bridge Service Account"

# 2. Grant Vertex AI User permission
gcloud projects add-iam-policy-binding [YOUR_PROJECT_ID] \
    --member="serviceAccount:vertex-mcp-sa@[YOUR_PROJECT_ID].iam.gserviceaccount.com" \
    --role="roles/aiplatform.user"
```

---

## 🚢 Step 3: Deploy to Cloud Run

Run the following command to build the image and deploy the service:

```bash
gcloud run deploy vertex-ai-bridge \
    --source . \
    --region us-central1 \
    --service-account vertex-mcp-sa@[YOUR_PROJECT_ID].iam.gserviceaccount.com \
    --no-allow-unauthenticated \
    --set-env-vars="GOOGLE_CLOUD_PROJECT=[YOUR_PROJECT_ID],GOOGLE_CLOUD_LOCATION=us-central1"
```

> **Note**: We use `--no-allow-unauthenticated` for security. Only users with valid Identity Tokens can access this server.

---

## 🔌 Step 4: Configure Your MCP Client

Once deployed, you will receive a **Service URL** (e.g., `https://vertex-ai-bridge-xyz.a.run.app`).

### For Claude Desktop or Cursor

Update your `claude_desktop_config.json` or Cursor MCP settings. Since the server is authenticated, you need to pass an Identity Token:

```json
{
  "mcpServers": {
    "vertex-ai-bridge": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/inspector",
        "--sse",
        "https://YOUR-SERVICE-URL.a.run.app/sse"
      ],
      "env": {
        "AUTHORIZATION": "bearer [YOUR_ID_TOKEN]"
      }
    }
  }
}
```

**To generate a token for local testing:**
```bash
gcloud auth print-identity-token
```

---

## 🧪 Step 5: Verification

You can test if the server is responding correctly using `curl`:

```bash
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
     https://YOUR-SERVICE-URL.a.run.app/sse
```

---

## 💡 Pro Tips
- **Cold Starts**: If you experience delays on the first request, consider setting a minimum number of instances (`--min-instances 1`), though this will incur costs.
- **Custom Domain**: You can map a custom domain to your Cloud Run service via the GCP Console.
