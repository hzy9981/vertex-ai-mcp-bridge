# Vertex AI & DashScope Bridge MCP サーバー

[![Official MCP List](https://img.shields.io/badge/MCP-Listed-blue)](https://modelcontextprotocol.io/examples/servers)
[![Deploy to Cloud Run](https://img.shields.io/badge/Deploy-Cloud%20Run-orange)](DEPLOY.md)
[![License](https://img.shields.io/badge/License-Apache%202.0-green.svg)](https://opensource.org/licenses/Apache-2.0)

[English](README.md) | [中文](README.zh.md) | [日本語](README.ja.md)

これは、Google Vertex AIの強力な機能をあなたのローカルAIアシスタントと連携させるための包括的なModel Context Protocol (MCP) サーバーです。プロンプト管理と自動最適化をサポートするだけでなく、クラウド間のツール調整をシームレスに実現します。

---

## 🚀 クイックリンク
- **[公式 MCP リスト](https://modelcontextprotocol.io/examples/servers)** ("Vertex AI Bridge" で検索)
- **[詳細なデプロイガイド (Cloud Run)](DEPLOY.md)** - わずか10分で本番環境デプロイを完了。

## ✨ 主な機能

- **マルチトランスポートプロトコルサポート**: 
  - `stdio`: Cursor、VS Code などのローカルIDEに最適。
  - `sse`: 標準 Server-Sent Events、Web クライアント向け。
  - `streamable-http`: **(New)** より堅牢なストリーミング HTTP プロトコル、クラウド長接続向け。
  - `hybrid`: **(New)** 複数のプロトコルを同時に起動し、異なる統合ニーズに対応。
- **リモート SSE プロキシモード**: ローカルツール (Cursor など) がリモート SSE に非対応でも、`remote_sse` トランスポート経由でクラウドサービスをローカルに透過的にブリッジできます。
- **包括的なプロンプトエンジニアリング**: Vertex AI プロンプト管理の CRUD と最先端のデータ駆動型最適化ツールが組み込まれています。
- **クロスクラウドツールプロキシ**: `call_dashscope_mcp` 経由でリモート DashScope サービスを直接呼び出すことが可能。

## 🛠 提供されるツール

| ツールカテゴリー | ツール名 | 説明 |
| :--- | :--- | :--- |
| **プロンプト CRUD** | `create_prompt`, `read_prompt`, `update_prompt`, `list_prompts`, `delete_prompt` | Vertex AI プロンプトの完全なライフサイクル管理 |
| **最適化** | `run_few_shot_optimization`, `run_data_driven_optimize`, `analyze_data_driven_optimize_results` | フューショット及びデータ駆動型の自動プロンプト最適化 |
| **プロキシ** | `call_dashscope_mcp` | リモート DashScope MCP ツールへのプロキシ呼び出し |

## 🚀 デプロイと実行

### 1. クラウドデプロイ (Cloud Run)
提供されている完全自動デプロイスクリプトを直接実行：
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh
```

### 2. ローカルプロキシモード (デプロイ済みサービスへの接続)
クライアント (Cursor など) がローカル Stdio コマンドラインのみに対応しているが、クラウド上にデプロイされたサービスを使用したい場合：
```bash
python -m vertex.server --transport remote_sse --remote_sse_url https://YOUR-CLOUD-RUN-URL/sse
```

## 💻 クライアント統合の例

### Cursor / Claude Desktop (Stdio)
```json
{
  "mcpServers": {
    "vertex-bridge": {
      "command": "/home/hzy9981/vertex-ai-mcp-bridge-local/.venv/bin/python3",
      "args": ["-m", "vertex.server", "--transport", "stdio"],
      "env": {
        "GOOGLE_CLOUD_PROJECT": "your-project-id",
        "DASHSCOPE_API_KEY": "your-key"
      }
    }
  }
}
```

## 📄 ライセンス
[Apache-2.0 License](LICENSE)
