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
| **生成 API** | `generate_with_vertex`, `generate_with_deepseek` | Vertex AI Gemini モデル (gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite) と DeepSeek (deepseek-flash, deepseek-v4-pro) による汎用テキスト生成 |

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
        "DASHSCOPE_API_KEY": "your-key",
        "DEEPSEEK_API_KEY": "your-key"
      }
    }
  }
}
```

### 生成 API の使用例
```python
# Vertex AI (Gemini)
result = await session.call_tool("generate_with_vertex", {"prompt": "こんにちは", "model": "gemini-2.5-flash", "temperature": 0.7, "max_tokens": 512, "system_instruction": "簡潔に答えてください。"})

# DeepSeek (DEEPSEEK_API_KEY が必要)
result = await session.call_tool("generate_with_deepseek", {"prompt": "こんにちは", "model": "deepseek-flash"})
```
どちらも `text`、`model`、`finish_reason`、`input_tokens`、`output_tokens` を返し、トークン使用量統計に記録されます。

### OpenAI 互換 API (`/v1/chat/completions`)

サービスに環境変数 `OPENAI_COMPATIBLE_API_KEY`（複数の場合はカンマ区切り）を設定します。未設定の場合、このルートは 501 を返します。クライアントは `Authorization: Bearer <key>` を送信します。モデル名のプレフィックスでルーティングされます：`gemini-*` → Vertex AI、`deepseek-*` → DeepSeek。クライアントの Base URL に Cloud Run のサービス URL（例：`https://<service>.run.app/v1`）を設定してください。

```bash
curl -X POST "$SERVICE_URL/v1/chat/completions" \
  -H "Authorization: Bearer $OPENAI_COMPATIBLE_API_KEY" -H "Content-Type: application/json" \
  -d '{"model": "gemini-2.5-flash", "messages": [{"role": "user", "content": "こんにちは！"}], "stream": false}'
```

`stream=true` は `text/event-stream` を返します（完全な応答の生成後にチャンク送信）。エラー：400 不正なリクエスト、401 キー無効、404 モデル不明、500 上流エラー。

## 📄 ライセンス
[Apache-2.0 License](LICENSE)
