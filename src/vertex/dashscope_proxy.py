"""Module for DashScope MCP proxy tool."""

import os
from mcp.server import fastmcp
from mcp.client.session import ClientSession
from mcp.client.sse import sse_client

def register_dashscope_tools(mcp: fastmcp.FastMCP):
    """Register DashScope proxy tools to the MCP server."""

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
                return str(result.content)

if __name__ == "__main__":
    mcp = fastmcp.FastMCP("DashScopeProxy")
    register_dashscope_tools(mcp)
    mcp.run()
