import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from tools.tool_recent_logins import get_recent_logins

"""
This file is the main MCP Server file, it creates the folder, defines tool frameworks and calls individual tools by calling
their function.

Tool logic should not be placed in here, create a seperate file for tools under the "tools" directory, all tool files should
follow naming scheme tool_ 
"""
load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

app = Server("OpsReady-server")


@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_recent_logins",
            description="Returns users who have logged in since certain date (YYYY-MM-DD)",
            inputSchema={
                "type": "object",
                "properties": {
                    "since_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    }
                },
                "required": ["since_date"]
            }
        ),
        Tool(
            name="get_assigned_tasks",
            description="Return the tasks that are assigned to a user, all, due, upcoming",
            inputSchema={
                "type": "object",
                "properties": {
                    "query_type": {
                        "type": "string",
                        "enum": ["list_all", "overdue", "upcoming"],
                            "description": (
                            "Type of query to run: "
                            "'list_all' (all tasks), 'overdue' (past due_date), "
                            "or 'upcoming' (due soon)."
                        )
                    },

                },
                "required": ["query_type"]
            }
        ),
        Tool(
            name="get_unresolved_asset_count",
            description="Returns the total count of assets with unresolved deficiencies for a given workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_id": {
                        "type": "string",
                        "description": "The ID of the main OpsReady workspace to analyze."
                    }
                },
                "required": ["workspace_id"]
            }
        ),
        Tool(
            name="get_workspace_forms",
            description="Returns all available forms (and their IDs) for a specific OpsReady workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_name": {
                        "type": "string",
                        "description": "The name of the OpsReady workspace (e.g., 'Summit Base')."
                    }
                },
                "required": ["workspace_name"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_recent_logins":
        return await get_recent_logins(arguments["since_date"])

    elif name == "get_workspace_forms":
        from tools.tool_list_forms import get_workspace_forms_tool
        return await get_workspace_forms_tool(arguments["workspace_name"])



















async def main():
    from mcp.server.stdio import stdio_server
    print("Server running")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    print("Starting OpsReady MCP Server...")
    asyncio.run(main())
