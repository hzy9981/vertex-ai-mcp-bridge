# Vertex AI & DashScope Bridge MCP Server

[![MCP Specification](https://img.shields.io/badge/MCP-Standard-blue)](https://modelcontextprotocol.io)
[![Deploy to Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-orange)](https://cloud.google.com/run)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

这是一个全能型的 Model Context Protocol (MCP) 服务器，旨在连接 Google Vertex AI 的强大能力与您的本地 AI 助手。它不仅支持提示词管理与自动化优化，还集成了跨平台的工具代理（如阿里云 DashScope）。

## ✨ 核心特性

- **多传输协议支持**: 
  - `stdio`: 最适合 Cursor, VS Code 等本地 IDE。
  - `sse`: 标准 Server-Sent Events，适用于 Web 客户端。
  - `streamable-http`: **(New)** 更健壮的流式 HTTP 协议，适合云端长连接。
  - `hybrid`: **(New)** 同时启动多种协议，适配不同集成需求。
- **远程 SSE 代理模式**: 即使您的本地工具（如 Cursor）不支持远程 SSE，您也可以通过 `remote_sse` 传输方式将云端服务透明地桥接到本地。
- **全方位提示词工程**: 内置 Vertex AI Prompt Management 的 CRUD 及其最前沿的数据驱动优化工具。
- **跨云工具代理**: 支持通过 `call_dashscope_mcp` 直接调用远程 DashScope 服务。

## 🛠 提供的工具

| 工具类别 | 工具名称 | 功能描述 |
| :--- | :--- | :--- |
| **Prompt CRUD** | `create_prompt`, `read_prompt`, `update_prompt`, `list_prompts`, `delete_prompt` | Vertex AI 提示词的全生命周期管理 |
| **Optimization** | `run_few_shot_optimization`, `run_data_driven_optimize`, `analyze_data_driven_optimize_results` | 少样本及数据驱动的提示词自动调优 |
| **Proxy** | `call_dashscope_mcp` | 代理调用远程 DashScope MCP 工具 |

## 🚀 部署与运行

### 1. 云端部署 (Cloud Run)
直接运行我们提供的全自动部署脚本：
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh
```

### 2. 本地代理模式 (连接到已部署的服务)
如果您的客户端（如 Cursor）只支持本地 Stdio 命令行，但您希望使用云端部署好的服务：
```bash
python -m vertex.server --transport remote_sse --remote_sse_url https://YOUR-CLOUD-RUN-URL/sse
```

## 💻 客户端集成示例

### Cursor / Claude Desktop (Stdio)
```json
{
  "mcpServers": {
    "vertex-bridge": {
      "command": "python",
      "args": ["-m", "vertex.server", "--transport", "stdio"],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "your-project-id",
        "DASHSCOPE_API_KEY": "your-key"
      }
    }
  }
}
```

## 📄 开源协议
[Apache-2.0 License](LICENSE)
