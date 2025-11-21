import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from tools.tool_recent_logins import get_recent_logins
from tools.tool_get_user_tasks import get_user_tasks
from tools.tool_debug_tasks_sample import get_task_sample
from tools.tool_get_all_assigned_users import get_all_assigned_users
from tools.tool_get_overdue_tasks import get_overdue_tasks
from tools.tool_get_task_summary_report import get_task_summary_report
from tools.tool_work_orders import get_work_orders


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
    name="get_user_tasks",
    description="Get all tasks assigned to a specific user by name, username, or email.",
    inputSchema={
        "type": "object",
        "properties": {
            "identifier": {
                "type": "string",
                "description": "Name, username, or email of the user to fetch tasks for."
            }
        },
        "required": ["identifier"]
    }
  ),

         Tool(
    name="get_task_sample",
    description="Return a small sample of tasks with basic fields for debugging.",
    inputSchema={
        "type": "object",
        "properties": {
            "limit": {
                "type": "integer",
                "description": "How many tasks to show (default 5)."
            }
        },
        "required": []
    }
),
Tool(
    name="get_all_assigned_users",
    description="List all users who currently have one or more tasks assigned, with task counts.",
    inputSchema={"type": "object", "properties": {}}
),
Tool(
    name="get_overdue_tasks",
    description="List all tasks whose due date is before today (UTC).",
    inputSchema={"type": "object", "properties": {}}
),
Tool(
    name="get_task_summary_report",
    description="Generate a summary report of all OpsReady tasks: total, assigned/unassigned, overdue, due soon, and category breakdown.",
    inputSchema={"type": "object", "properties": {}}
),
Tool(
    name="get_work_orders",
    description="Get work orders with optional status filter.",
    inputSchema={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "description": "Status of work orders to filter by (e.g., 'Open', 'Closed')."
            }
        },
        "required": []
    }
)



         ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_recent_logins":
        return await get_recent_logins(arguments["since_date"])
    if name == "get_user_tasks":
        return await get_user_tasks(arguments["identifier"])
    if name == "get_task_sample":
        return await get_task_sample(arguments.get("limit", 5))
    if name == "get_all_assigned_users":
        return await get_all_assigned_users()
    if name == "get_overdue_tasks":
        return await get_overdue_tasks()
    if name == "get_task_summary_report":
        return await get_task_summary_report()
    if name == "get_work_orders":
        status = arguments.get("status")
        return await get_work_orders(status=status)






    #elif name == "get_assigned_tasks":   //demonstrating how tool calls will work
        return null

async def main():
    from mcp.server.stdio import stdio_server
    print("Server running")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    print("Starting OpsReady MCP Server...")
    asyncio.run(main())