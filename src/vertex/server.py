"""Module for defining tools for the CLI agent."""

import os
import sys
from collections.abc import Sequence

from absl import app, flags
from mcp.server import fastmcp

from . import tools
from .prompt_optimizer import analyzer, prompt_optimizer

FLAGS = flags.FLAGS

flags.DEFINE_enum(
    "transport", "stdio", ["stdio", "sse", "remote_sse", "streamable-http", "hybrid"], "Transport method for MCP server."
)
flags.DEFINE_string("remote_sse_url", "https://vertex-mcp-server-1069561025565.us-central1.run.app/sse", "URL for remote SSE MCP server.")
flags.DEFINE_integer("port", int(os.environ.get("PORT", 8080)), "Port for SSE.")


async def run_remote_proxy():
    from mcp.client.session import ClientSession
    from mcp.client.sse import sse_client
    from mcp.server.stdio import stdio_server
    import asyncio

    url = FLAGS.remote_sse_url
    print(f"Connecting to remote MCP server at {url}...", file=sys.stderr)
    
    # 1. Setup SSE connection to remote server
    async with sse_client(url) as (remote_read, remote_write):
        # 2. Setup Stdio transport for local CLI/Cursor
        async with stdio_server() as (local_read, local_write):
            # 3. Define a bridge that forwards messages (not raw bytes)
            
            async def forward(reader, writer, name):
                try:
                    async for message in reader:
                        if isinstance(message, Exception):
                            print(f"Exception in {name} stream: {message}", file=sys.stderr)
                            continue
                        await writer.send(message)
                except Exception as e:
                    if "ClosedResourceError" not in str(e):
                        print(f"Error in {name} forwarding: {e}", file=sys.stderr)

            # Start bidirectional forwarding
            print("Bridge active. Forwarding traffic...", file=sys.stderr)
            await asyncio.gather(
                forward(local_read, remote_write, "local->remote"),
                forward(remote_read, local_write, "remote->local")
            )


def main(argv: Sequence[str]) -> None:
    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    if FLAGS.transport == "remote_sse":
        import asyncio
        asyncio.run(run_remote_proxy())
        return

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

    # --- 自定义 HTTP 路由 (支持简单的 HTTP 调用和 Streaming) ---
    from starlette.responses import JSONResponse, StreamingResponse
    import json
    import asyncio

    @mcp.custom_route("/", methods=["GET", "POST"])
    async def root_handler(request):
        """处理根路径请求，支持用户之前的 curl 测试。"""
        if request.method == "POST":
            try:
                data = await request.json()
            except Exception:
                data = {}
            name = data.get("name", "Developer")
            return JSONResponse({
                "message": f"Hello, {name}!",
                "status": "Vertex AI MCP Bridge is running",
                "available_tools": [t.name for t in mcp._tool_manager.list_tools()]
            })
        return JSONResponse({"message": "Vertex AI MCP Bridge is running. Use /sse for MCP SSE or /mcp for Streamable HTTP."})

    @mcp.custom_route("/call/{tool_name}", methods=["POST"])
    async def call_tool_stream(request):
        """通过简单的 HTTP POST 调用工具并支持以 SSE 格式返回结果。"""
        tool_name = request.path_params["tool_name"]
        try:
            arguments = await request.json()
        except Exception:
            arguments = {}
        
        async def event_generator():
            try:
                # 首先发送一个开始事件
                yield f"event: start\ndata: {json.dumps({'tool': tool_name})}\n\n"
                
                # 调用工具
                result = await mcp.call_tool(tool_name, arguments)
                
                # 发送结果事件
                yield f"event: result\ndata: {json.dumps(result, default=str)}\n\n"
            except Exception as e:
                yield f"event: error\ndata: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
    # --------------------------------------------------------

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

    if FLAGS.transport in ["sse", "streamable-http", "hybrid"]:
        import uvicorn
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.routing import Route, Mount
        from starlette.middleware.trustedhost import TrustedHostMiddleware

        # 1. 准备 SSE 传输
        sse_transport = SseServerTransport("/messages")

        async def handle_sse(request):
            async with sse_transport.connect_sse(
                request.scope, request.receive, request._send
            ) as (read_stream, write_stream):
                await mcp._mcp_server.run(
                    read_stream,
                    write_stream,
                    mcp._mcp_server.create_initialization_options(),
                )

        # 2. 获取内置了 Lifespan 处理的 Streamable HTTP 应用作为基础
        # 这样可以确保 TaskGroup 被正确初始化，解决 "Task group is not initialized" 错误
        starlette_app = mcp.streamable_http_app()

        # 3. 将 SSE 路由和自定义路由添加到该应用中
        starlette_app.add_route("/sse", handle_sse)
        starlette_app.mount("/messages", app=sse_transport.handle_post_message)

        # 合并自定义路由 (例如 / 和 /call)
        for route in mcp._custom_starlette_routes:
            starlette_app.routes.append(route)

        web_app = TrustedHostMiddleware(starlette_app, allowed_hosts=["*"])

        print(f"Starting unified server in {FLAGS.transport} mode on port {FLAGS.port}")
        uvicorn.run(
            web_app,
            host="0.0.0.0",
            port=FLAGS.port,
            proxy_headers=True,
            forwarded_allow_ips="*",
        )
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    app.run(main)
