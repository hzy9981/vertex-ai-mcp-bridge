# 📦 Vertex AI Bridge MCP Server - Press Kit (素材包)

这个文件包含了发布 Vertex AI Bridge MCP Server 到各个平台所需的所有文案和素材。

---

## 0. 项目基础信息 (Essentials)
- **项目全称**: Vertex AI & DashScope Bridge MCP Server
- **GitHub 地址**: https://github.com/hzy9981/vertex-ai-mcp-bridge
- **一句话简介**: 
    - **EN**: A standardized bridge to bring Google Vertex AI's Gemini 2.0 and Search Grounding capabilities into any MCP-compatible environment like Cursor and Claude.
    - **ZH**: 一个全能型 MCP 服务器，将 Google Vertex AI 的强大能力（Gemini 2.0/搜索增强）与您的本地 AI 助手（Cursor/Claude）无缝连接。

---

## 1. Reddit 推广文案 (r/GoogleCloud, r/Cursor)

**Title**: [Showcase] Vertex AI Bridge: Bringing Gemini 2.0 & Search Grounding to the MCP Ecosystem

**Body**:
Hi GCP Community,

I’ve always wanted a way to bring Gemini 2.0 Pro/Flash and Google Search Grounding directly into my daily coding workflow (Cursor IDE) and AI clients (Claude Desktop). 

So I built **Vertex AI Bridge**, an MCP (Model Context Protocol) server that acts as a secure, standardized gateway to Google Cloud's Vertex AI platform. It’s now officially listed on the MCP servers directory!

### 🌟 Key Features:
- **Search Grounding**: Use the `answer_query_websearch` tool to get real-time answers backed by Google Search inside Cursor/Claude.
- **Gemini 2.0 Access**: Leverage Gemini's massive 2M context window for full-repo analysis.
- **IAM-Native Security**: Built with enterprise security in mind, leveraging Google Cloud IAM.
- **Serverless Ready**: Optimized for deployment on **Cloud Run** with SSE support.

### 🚀 Quick Deployment:
I just added a comprehensive deployment guide to the repo. You can get your own private Vertex AI bridge running on Cloud Run in minutes:
https://github.com/hzy9981/vertex-ai-mcp-bridge/blob/main/DEPLOY.md

**Repo**: https://github.com/hzy9981/vertex-ai-mcp-bridge

---

## 2. Medium 文章引言 (Introduction)

**Title**: Beyond the Chatbox: Connecting Google Vertex AI to the World via MCP

**Introduction**:
Imagine you’re in the middle of a complex refactor in Cursor. You hit a wall with a legacy library, and the AI starts hallucinating a version that doesn’t exist. You wish your assistant could just “Google it” or tap into the massive 2M context window of Gemini 2.0 Pro without you having to switch tabs.

The reality for many developers today is fragmentation. We have the UIs we love — like Claude Desktop or Cursor — but the enterprise-grade power we need often resides behind the robust, yet separate, walls of Google Cloud Vertex AI. 

Today, I’m excited to share **Vertex AI Bridge**: a project I developed to bring the best of Google Cloud — including Search Grounding and the latest Gemini models — directly into any MCP-compatible environment.

---

## 3. Google Cloud 论坛文案 (GCP Community)

**Headline**: [Community Showcase] Vertex AI Bridge: Bringing Gemini 2.0 & Search Grounding to the MCP Ecosystem

**Highlights**:
- **Why this matters**: Brings enterprise Gemini capabilities into the rapid-growing MCP ecosystem (Cursor, Windsurf, Claude).
- **Architecture**: Optimized for Cloud Run using SSE transport for a serverless, pay-per-use model.
- **Security**: Leverages Google Cloud Identity Tokens and Service Accounts.

---

## 4. 极速配置代码 (For Users)

```json
"vertex-ai-bridge": {
  "command": "npx",
  "args": [
    "-y", 
    "@modelcontextprotocol/inspector", 
    "--sse", 
    "https://[YOUR-SERVICE-URL].a.run.app/sse"
  ],
  "env": {
    "AUTHORIZATION": "bearer $(gcloud auth print-identity-token)"
  }
}
```

---

## 5. 开发者建议 (Pro-Tips)
- **视觉优先**: 发布时务必配上 Cursor 中调用 Search Grounding 的 GIF 截图。
- **求 Star**: 在回复用户反馈时，顺带求 Star：“If this helps, a ⭐️ on GitHub would be much appreciated!”
