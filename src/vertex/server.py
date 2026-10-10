"""Module for defining tools for the CLI agent."""

import asyncio
import json
import os
import sys
from collections.abc import Sequence

import uvicorn
from absl import app, flags, logging as absl_logging
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client
from mcp.server import fastmcp
from mcp.server.sse import SseServerTransport
from mcp.server.stdio import stdio_server
from starlette.responses import JSONResponse, StreamingResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from . import tools
from . import usage_tracker
from .deepseek_client import DeepSeekClient
from .openai_compat import handle_chat_completions
from .prompt_optimizer import analyzer, prompt_optimizer
from .vertex_generative_client import VertexGenerativeClient

FLAGS = flags.FLAGS

flags.DEFINE_enum(
    "transport", "stdio", ["stdio", "sse", "remote_sse", "streamable-http", "hybrid"], "Transport method for MCP server."
)
flags.DEFINE_string("remote_sse_url", "https://vertex-mcp-server-1069561025565.us-central1.run.app/sse", "URL for remote SSE MCP server.")
flags.DEFINE_integer("port", int(os.environ.get("PORT", 8080)), "Port for SSE.")


async def run_remote_proxy():
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
    # Ensure all logs go to stderr to avoid polluting stdout (important for MCP)
    absl_logging.set_stderrthreshold('info')

    if len(argv) > 1:
        raise app.UsageError("Too many command-line arguments.")

    if FLAGS.transport == "remote_sse":
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
    transport_security = getattr(mcp.settings, "transport_security", None)
    if transport_security:
        transport_security.enable_dns_rebinding_protection = False

    # --- 自定义 HTTP 路由 (支持简单的 HTTP 调用和 Streaming) ---

    @mcp.custom_route("/ping", methods=["GET"])
    async def ping_handler(request):
        """Health check route for Glama/Cloud Run."""
        return JSONResponse({"status": "ok"})

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

    @mcp.custom_route("/v1/chat/completions", methods=["POST"])
    async def openai_chat_completions(request):
        """OpenAI 兼容的 Chat Completions 接口 (需要 OPENAI_COMPATIBLE_API_KEY)。"""
        return await handle_chat_completions(request, mcp.call_tool)
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

    # --- Usage Statistics Tool ---
    @mcp.tool()
    async def get_token_usage_stats() -> dict:
        """获取 MCP 服务的 token 使用统计信息。"""
        return usage_tracker.get_stats()

    # --- 通用模型生成 API (Vertex AI / DeepSeek) ---
    vertex_gen_client = VertexGenerativeClient(
        project_id=project_id, location=location_id
    )
    deepseek_client = DeepSeekClient()

    @mcp.tool()
    async def generate_with_vertex(
        prompt: str,
        model: str = "gemini-2.5-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        top_k: int = 40,
        system_instruction: str | None = None,
    ) -> dict:
        """使用 Vertex AI Gemini 模型生成文本。

        Args:
            prompt: 用户提示词
            model: gemini-2.5-flash (默认), gemini-2.5-pro 或 gemini-2.5-flash-lite；其他名称会交由 Vertex 校验
            temperature: 生成多样性
            max_tokens: 最大输出 token 数。注意：Gemini 2.5 的 "thinking" token 也计入此上限，
                过小的值（如 512）可能截断可见回答，建议 1024 以上
            top_p: Top-P 采样参数
            top_k: Top-K 采样参数
            system_instruction: 系统指令
        """
        result = await vertex_gen_client.generate_content(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            top_k=top_k,
            system_instruction=system_instruction,
        )
        usage_tracker.log_usage(
            tool_name="generate_with_vertex",
            model_name=model,
            input_text=(system_instruction or "") + prompt,
            output_text=result["text"],
        )
        return result

    @mcp.tool()
    async def generate_with_deepseek(
        prompt: str,
        model: str = "deepseek-flash",
        temperature: float = 0.7,
        max_tokens: int = 1024,
        top_p: float = 0.95,
        system_instruction: str | None = None,
    ) -> dict:
        """使用 DeepSeek API 生成文本 (需要 DEEPSEEK_API_KEY)。

        Args:
            prompt: 用户提示词
            model: deepseek-flash 或 deepseek-v4-pro
            temperature: 生成多样性
            max_tokens: 最大输出 token 数
            top_p: Top-P 采样参数
            system_instruction: 系统指令
        """
        result = await deepseek_client.generate_content(
            prompt=prompt,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            top_p=top_p,
            system_instruction=system_instruction,
        )
        usage_tracker.log_usage(
            tool_name="generate_with_deepseek",
            model_name=model,
            input_text=(system_instruction or "") + prompt,
            output_text=result["text"],
        )
        return result

    # --- 集成 DashScope MCP ---
    @mcp.tool()
    async def call_dashscope_mcp(tool_name: str, arguments: dict) -> str:
        """调用 DashScope 的远程 MCP 服务并获取结果。
        
        Args:
            tool_name: DashScope MCP 中的工具名称
            arguments: 传递给工具的参数字典
        """
        api_key = os.environ.get("DASHSCOPE_API_KEY")
        if not api_key:
            return "错误: 未设置 DASHSCOPE_API_KEY 环境变量。"
        
        url = "https://dashscope.aliyuncs.com/api/v1/mcps/mcp-MmZlNzMyZTFjNmRj/mcp"
        headers = {"Authorization": f"Bearer {api_key}"}

        async with sse_client(url, headers=headers) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                result = await session.call_tool(tool_name, arguments)
                res_str = str(result.content)
                
                # Log usage
                usage_tracker.log_usage(
                    tool_name=f"dashscope:{tool_name}",
                    model_name="dashscope-remote",
                    input_text=json.dumps(arguments),
                    output_text=res_str
                )
                
                return res_str
    # --------------------------

    if FLAGS.transport in ["sse", "streamable-http", "hybrid"]:
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

        print(f"Starting unified server in {FLAGS.transport} mode on port {FLAGS.port}", file=sys.stderr)
        
        # Configure uvicorn logging to stderr
        log_config = uvicorn.config.LOGGING_CONFIG
        log_config["handlers"]["default"]["stream"] = "ext://sys.stderr"
        log_config["handlers"]["access"]["stream"] = "ext://sys.stderr"
        
        uvicorn.run(
            web_app,
            host="0.0.0.0",
            port=FLAGS.port,
            proxy_headers=True,
            forwarded_allow_ips="*",
            log_config=log_config,
        )
    else:
        mcp.run(transport="stdio")


def main_entry() -> None:
    """Entry point for the console script."""
    app.run(main)


if __name__ == "__main__":
    main_entry()
