# Deployment Status

## ✅ Completed

**Date:** 2026-10-10  
**Commit:** PR #4 merged - Switch Vertex default to gemini-2.5-flash, fix deploy script, repair test suite

### Changes
- ✅ Vertex AI models updated: `gemini-2.5-flash` (default), `gemini-2.5-pro`, `gemini-2.5-flash-lite`
- ✅ Deprecated models removed: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
- ✅ Unknown model names now pass through to Vertex AI (no breaking changes on new releases)
- ✅ `deploy_cloud_run.sh` fixed: correct continuations, service name `vertex-mcp-server`, env vars
- ✅ Test suite repaired: 27 tests passing
- ✅ Documentation updated: README EN/ZH/JA

### Available Tools
- `generate_with_vertex` - Vertex AI Gemini models (gemini-2.5-flash, gemini-2.5-pro, gemini-2.5-flash-lite)
- `generate_with_deepseek` - DeepSeek models (deepseek-flash, deepseek-v4-pro)
- Legacy prompt management tools (create, read, update, delete, list)
- Legacy optimizer tools

### Cloud Run Service
- **URL:** https://vertex-mcp-server-1069561025565.us-central1.run.app
- **Region:** us-central1
- **Project:** graceful-tenure-298505
- **Status:** Ready for redeploy from main

### Next Steps
1. Redeploy from main to pick up all changes
2. Test with `gemini-2.5-flash` (default)
3. Verify `deepseek-flash` continues to work

### Notes
- Gemini 2.5 thinking tokens count against `max_tokens`; use 1024+ for complete answers
- Unknown model names will log a warning but still be passed to Vertex AI
- Tests verified locally; no live API testing performed
