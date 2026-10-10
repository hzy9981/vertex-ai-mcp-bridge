"""Manual tests that call the real APIs.

Usage:
    DEEPSEEK_API_KEY=sk-xxx python tests/manual_test.py
    GOOGLE_CLOUD_PROJECT=xxx python tests/manual_test.py
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from vertex.deepseek_client import SUPPORTED_MODELS, DeepSeekClient  # noqa: E402
from vertex.vertex_generative_client import VertexGenerativeClient  # noqa: E402

PROMPT = "Say hello in one short sentence."


async def check_deepseek() -> bool:
    if not os.environ.get("DEEPSEEK_API_KEY"):
        print("[SKIP] DeepSeek: DEEPSEEK_API_KEY not set")
        return True
    for model in SUPPORTED_MODELS:
        try:
            result = await DeepSeekClient().generate_content(
                PROMPT, model=model
            )
            print(f"[OK] DeepSeek {model}: {result['text'][:50]}...")
        except Exception as e:
            print(f"[FAIL] DeepSeek {model}: {e}")
            return False
    return True


async def check_vertex() -> bool:
    if not os.environ.get("GOOGLE_CLOUD_PROJECT"):
        print("[SKIP] Vertex: GOOGLE_CLOUD_PROJECT not set")
        return True
    try:
        result = await VertexGenerativeClient().generate_content(PROMPT)
        print(f"[OK] Vertex: {result['text'][:50]}...")
        return True
    except Exception as e:
        print(f"[FAIL] Vertex: {e}")
        return False


async def main() -> int:
    results = [await check_deepseek(), await check_vertex()]
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(asyncio.run(main()))
