# Vertex AI & DashScope Bridge MCP Server

[![MCP Specification](https://img.shields.io/badge/MCP-Standard-blue)](https://modelcontextprotocol.io)
[![Deploy to Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-orange)](https://cloud.google.com/run)

这是一个高性能的 Model Context Protocol (MCP) 服务器，支持部署在 Google Cloud Run 并通过 SSE (Server-Sent Events) 提供服务。它不仅支持原生的 Vertex AI 提示词管理，还集成了一个强大的代理工具，用于调用阿里云 DashScope 的 MCP 服务。

## 🌟 核心特性

- **多服务集成**: 同时接入 Google Vertex AI 和阿里云 DashScope 工具集。
- **云端原生**: 专为 Google Cloud Run 优化，支持自动扩缩容。
- **SSE 传输**: 支持基于 HTTP 的 SSE 协议，完美兼容 Cherry Studio, Claude Desktop 等客户端。
- **提示词工程**: 内置 Vertex AI 提示词 CRUD 管理及自动化优化工具。

## 🛠 提供的工具

### Vertex AI 管理
- `create_prompt`: 保存新提示词到 Vertex AI。
- `read_prompt`: 按 ID 获取提示词内容。
- `update_prompt`: 修改现有提示词。
- `list_prompts`: 搜索并列出所有提示词。

### 自动化优化
- `run_few_shot_optimization`: 基于示例进行少样本提示词优化。
- `run_data_driven_optimize`: 启动大规模数据驱动的提示词优化任务。
- `analyze_data_driven_optimize_results`: 深入分析优化结果。

### 跨平台代理
- `call_dashscope_mcp`: **核心功能**。通过代理方式调用远程的 DashScope MCP 服务。

## 🚀 快速部署 (Cloud Run)

本项目包含自动化部署脚本 `deploy.sh`。

### 前提条件
1. 已安装 [Google Cloud SDK (gcloud)](https://cloud.google.com/sdk)。
2. 拥有一个已启用结算功能的 GCP 项目。

### 部署步骤
1. 克隆代码库。
2. 设置必要的环境变量（仅限本地部署环境）：
   ```bash
   export DASHSCOPE_API_KEY="您的阿里云API密钥"
   ```
3. 运行部署脚本：
   ```bash
   chmod +x deploy.sh
   ./deploy.sh
   ```
4. 部署成功后，脚本会输出 **Service URL**。

## 💻 客户端配置 (以 Cherry Studio 为例)

1. 进入 **设置 -> MCP**。
2. 点击 **添加**，选择类型为 **SSE**。
3. **URL**: 输入部署得到的服务 URL 加上 `/sse` 后缀。
   - 示例: `https://your-service-url.a.run.app/sse`
4. **无需额外 Header**: 密钥已安全存储在云端环境变量中。

## ⚙️ 环境变量说明

| 变量名 | 说明 |
| :--- | :--- |
| `GOOGLE_CLOUD_PROJECT` | GCP 项目 ID |
| `GOOGLE_CLOUD_LOCATION` | GCP 区域 (默认 us-central1) |
| `DASHSCOPE_API_KEY` | 阿里云 DashScope API 密钥 |

## 🛡 安全声明
本项目不硬编码任何 API 密钥。所有敏感信息均通过环境变量注入。建议定期轮换您的 API Key 以确保安全。

## 📄 开源协议
[Apache-2.0 License](LICENSE)
