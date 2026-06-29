"""Module for Vertex AI MCP server."""

import os
from absl import app, flags
from mcp.server import fastmcp
from . import tools
from .prompt_optimizer import analyzer, prompt_optimizer

FLAGS = flags.FLAGS

def main(argv):
    prompt_manager = tools.VertexPromptManager()
    project_id = os.environ.get("GOOGLE_CLOUD_PROJECT") or ""
    location_id = os.environ.get("GOOGLE_CLOUD_LOCATION") or "us-central1"
    optimizer_tools = prompt_optimizer.PromptOptimizer(
        project=project_id, location=location_id
    )

    mcp = fastmcp.FastMCP("VertexAI-Prompt-Manager")

    mcp.add_tool(prompt_manager.read_prompt)
    mcp.add_tool(prompt_manager.create_prompt)
    mcp.add_tool(prompt_manager.update_prompt)
    mcp.add_tool(prompt_manager.delete_prompt)
    mcp.add_tool(prompt_manager.list_prompts)

    mcp.add_tool(optimizer_tools.write_config, name="write_data_driven_optimize_config")
    mcp.add_tool(optimizer_tools.run_data_driven_optimize, name="run_data_driven_optimize")
    mcp.add_tool(optimizer_tools.run_few_shot_optimization, name="run_few_shot_optimization")
    mcp.add_tool(analyzer.analyze_results, name="analyze_data_driven_optimize_results")
    mcp.add_tool(analyzer.generate_report, name="generate_html_report")

    mcp.run()

if __name__ == "__main__":
    app.run(main)
