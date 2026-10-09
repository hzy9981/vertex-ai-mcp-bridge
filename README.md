# Vertex AI & DashScope Bridge MCP Server

[![Official MCP List](https://img.shields.io/badge/MCP-Listed-blue)](https://modelcontextprotocol.io/examples/servers)
[![Deploy to Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-orange)](DEPLOY.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md)

This is a comprehensive Model Context Protocol (MCP) server designed to bridge the powerful capabilities of Google Vertex AI with your local AI assistants. It not only supports prompt management and automatic optimization but also enables seamless cross-cloud tool coordination.

---

## 🚀 Quick Links
- **[Official MCP List](https://modelcontextprotocol.io/examples/servers)** (Search "Vertex AI Bridge")
- **[Detailed Deployment Guide (Cloud Run)](DEPLOY.md)** - Production-ready deployment in 10 minutes.

## ✨ Core Features

- **Multi-Transport Protocol Support**: 
  - `stdio`: Best for local IDEs like Cursor, VS Code.
  - `sse`: Standard Server-Sent Events, suitable for web clients.
  - `streamable-http`: **(New)** More robust streaming HTTP protocol for cloud long-lived connections.
  - `hybrid`: **(New)** Launch multiple protocols simultaneously to adapt to different integration needs.
- **Remote SSE Proxy Mode**: Even if your local tools (like Cursor) don't support remote SSE, you can transparently bridge cloud services to local via `remote_sse` transport.
- **Comprehensive Prompt Engineering**: Built-in CRUD for Vertex AI Prompt Management and state-of-the-art data-driven optimization tools.
- **Cross-Cloud Tool Proxy**: Support for directly calling remote DashScope services via `call_dashscope_mcp`.

## 🛠 Provided Tools

| Tool Category | Tool Name | Description |
| :--- | :--- | :--- |
| **Prompt CRUD** | `create_prompt`, `read_prompt`, `update_prompt`, `list_prompts`, `delete_prompt` | Full lifecycle management for Vertex AI prompts |
| **Optimization** | `run_few_shot_optimization`, `run_data_driven_optimize`, `analyze_data_driven_optimize_results` | Few-shot and data-driven automatic prompt optimization |
| **Proxy** | `call_dashscope_mcp` | Proxy calls to remote DashScope MCP tools |
| **Proxy** | `call_deepseek` | Call DeepSeek models (`deepseek-flash`, `deepseek-v4-pro`) via the OpenAI-compatible API; requires `DEEPSEEK_API_KEY` |

## 🚀 Deployment and Running

### 1. Cloud Deployment (Cloud Run)
Run our fully automated deployment script directly:
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh
```

### 2. Local Proxy Mode (Connect to Deployed Service)
If your client (like Cursor) only supports local Stdio command line but you want to use the cloud-deployed service:
```bash
python -m vertex.server --transport remote_sse --remote_sse_url https://YOUR-CLOUD-RUN-URL/sse
```

## 💻 Client Integration Examples

### Cursor / Claude Desktop (Stdio)
```json
{
  "mcpServers": {
    "vertex-bridge": {
      "command": "/home/hzy9981/vertex-ai-mcp-bridge-local/.venv/bin/python3",
      "args": ["-m", "vertex.server", "--transport", "stdio"],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "your-project-id",
        "DASHSCOPE_API_KEY": "your-key",
        "DEEPSEEK_API_KEY": "your-deepseek-key"
      }
    }
  }
}
```

## 📄 License
[Apache-2.0 License](LICENSE)
