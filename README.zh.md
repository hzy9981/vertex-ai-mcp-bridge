# Vertex AI & DashScope Bridge MCP 服务器

[![Official MCP List](https://img.shields.io/badge/MCP-Listed-blue)](https://modelcontextprotocol.io/examples/servers)
[![Deploy to Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-orange)](DEPLOY.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md)

这是一个全能型的 Model Context Protocol (MCP) 服务器，旨在连接 Google Vertex AI 的强大能力与您的本地 AI 助手。它不仅支持提示词管理与自动化优化，还集成了跨云工具协调的无缝对接能力。

---

## 🚀 快速链接
- **[官方 MCP 列表](https://modelcontextprotocol.io/examples/servers)** (搜索 "Vertex AI Bridge")
- **[详细部署指南 (Cloud Run)](DEPLOY.md)** - 10 分钟内完成生产级部署。

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
| **优化工具** | `run_few_shot_optimization`, `run_data_driven_optimize`, `analyze_data_driven_optimize_results` | 少样本及数据驱动的提示词自动调优 |
| **代理工具** | `call_dashscope_mcp` | 代理调用远程 DashScope MCP 工具 |
| **生成 API** | `generate_with_vertex`, `generate_with_deepseek` | 通过 Vertex AI Gemini 模型 (gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite) 与 DeepSeek (deepseek-flash, deepseek-v4-pro) 进行通用文本生成 |

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
      "command": "/home/hzy9981/vertex-ai-mcp-bridge-local/.venv/bin/python3",
      "args": ["-m", "vertex.server", "--transport", "stdio"],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "your-project-id",
        "DASHSCOPE_API_KEY": "your-key",
        "DEEPSEEK_API_KEY": "your-key"
      }
    }
  }
}
```

### 生成 API 使用示例
```python
# Vertex AI (Gemini)
result = await session.call_tool("generate_with_vertex", {"prompt": "你好", "model": "gemini-2.5-flash", "temperature": 0.7, "max_tokens": 512, "system_instruction": "请简洁回答。"})

# DeepSeek (需要设置 DEEPSEEK_API_KEY)
result = await session.call_tool("generate_with_deepseek", {"prompt": "你好", "model": "deepseek-flash"})
```
两者均返回 `text`、`model`、`finish_reason`、`input_tokens` 和 `output_tokens`，并计入 token 使用统计。

### OpenAI 兼容 API (`/v1/chat/completions`)

在服务上设置环境变量 `OPENAI_COMPATIBLE_API_KEY`（多个密钥用逗号分隔）；未设置时该路由返回 501。客户端需发送 `Authorization: Bearer <key>`。按模型名前缀路由：`gemini-*` → Vertex AI，`deepseek-*` → DeepSeek。在客户端中将 Base URL 设为 Cloud Run 服务地址（如 `https://<service>.run.app/v1`）。

```bash
curl -X POST "$SERVICE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_COMPATIBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": "你好！"}], "stream": false}'
```

`stream=true` 返回 `text/event-stream`（在完整响应生成后分块发送）。错误码：400 请求无效，401 密钥无效，404 模型不存在，500 上游失败。

## 📄 开源协议
[Apache-2.0 License](LICENSE)
