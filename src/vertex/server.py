"""Module for defining tools for the CLI agent."""

import os
from collections.abc import Sequence

from absl import app, flags
from mcp.server import fastmcp

from . import tools
from .prompt_optimizer import analyzer, prompt_optimizer

FLAGS = flags.FLAGS

flags.DEFINE_enum(
    "transport", "stdio", ["stdio", "sse"], "Transport method for MCP server."
)
flags.DEFINE_integer("port", int(os.environ.get("PORT", 8080)), "Port for SSE.")


def main(argv: Sequence[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    prompt_manager = tools.VertexPromptManager()

    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
    location_id = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    optimizer_tools = prompt_optimizer.PromptOptimizer(
        project=project_id, location=location_id
    )

    # Create an MCP server
    mcp = fastmcp.FastMCP("VertexMcpServer")

    # Disable DNS rebinding protection for Cloud Run
    mcp.settings.transport_security.enable_dns_rebinding_protection = False

    mcp.add_tool(prompt_manager.read_prompt)
    mcp.add_tool(prompt_manager.create_prompt)
    mcp.add_tool(prompt_manager.update_prompt)
    mcp.add_tool(prompt_manager.delete_prompt)
    mcp.add_tool(prompt_manager.list_prompts)

    mcp.add_tool(
        optimizer_tools.write_config, name="write_data_driven_optimize_config"
    )
    mcp.add_tool(
        optimizer_tools.run_data_driven_optimize,
        name="run_data_driven_optimize",
    )
    mcp.add_tool(
        optimizer_tools.run_few_shot_optimization,
        name="run_few_shot_optimization",
    )
    mcp.add_tool(
        analyzer.analyze_results, name="analyze_data_driven_optimize_results"
    )
    mcp.add_tool(analyzer.generate_report, name="generate_html_report")

    # --- 集成 DashScope MCP ---
    @mcp.tool()
    async def call_dashscope_mcp(tool_name: str, arguments: dict) -> str:
        """调用 DashScope 的远程 MCP 服务并获取结果。
        
        Args:
            tool_name: DashScope MCP 中的工具名称
            arguments: 传递给工具的参数字典
        """
        from mcp.client.session import ClientSession
        from mcp.client.sse import sse_client

        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return "错误: 未设置 DASHSCOPE_API_KEY 环境变量。"
        
        url = "https://dashscope.aliyuncs.com/api/v1/mcps/mcp-MmZlNzMyZTFjNmRj/mcp"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with sse_client(url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                return str(result.content)
    # --------------------------

    if FLAGS.transport == "sse":
        import uvicorn
        from starlette.middleware.trustedhost import TrustedHostMiddleware

        app = TrustedHostMiddleware(mcp.sse_app(), allowed_hosts=["*"])

        uvicorn.run(
            app,
            host="0.0.0.0",
            port=FLAGS.port,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    app.run(main)
