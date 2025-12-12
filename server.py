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
from tools.tool_task_asignee import get_task_assignee
from tools.tool_activity_feed import get_activity_feed
from tools.tool_list_forms import get_workspace_forms_tool
from tools.tool_get_asset_deficiencies import get_asset_deficiencies
from tools.tool_work_orders import get_work_orders
from tools.get_deficiency_details import get_deficiency_details
from tools.tool_get_assets import get_assets
from tools.tool_teams_tasks import get_team_tasks



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
            name="get_task_assignee",
            description=(
                "Retrieves task information from a given workspace. "
                "If the user asks for *unassigned tasks*, it returns only those with no assignee. "
                "Otherwise, it returns all tasks in the workspace, including those that are assigned."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_name": {
                        "type": "string",
                        "description": "The name of the workspace to get tasks from."
                    },
                    "unassigned_only": {
                        "type": "boolean",
                        "description": (
                            "Optional. If true, returns only tasks without an assigned user. "
                            "If false or omitted, returns all tasks."
                        ),
                        "default": False
                    }
                },
                "required": ["workspace_name"]
            }
        ),
        Tool(
            name="get_team_tasks",
            description=(
                "Get the tasks that are assigned to a team. "
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "team_name": {
                        "type": "string",
                        "description": "The name of the team to get tasks from."
                    }
                },
                "required": ["team_name"]
            }
        ),
        Tool(
            name="get_activity_feed",
            description="Returns the most active users in a workspace, who has submitted forms, and most active ",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_name": {
                        "type": "string",
                        "description": "Name of the workspace",
                    },
                    "unassigned_only": {
                        "type": "boolean",
                        "description": "If True, show only unassigned tasks",
                        "default": False

                    }
                },
                "required": ["workspace_name"]
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
        ),
        Tool(
            name="get_workspace_deficiencies",
            description="Fetches all deficiencies for a given workspace and lists their status.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_name": {
                        "type": "string",
                        "description": "The name of the workspace to fetch deficiencies for."
                    }
                },
                "required": ["workspace_name"]
            }
        ),
        Tool(
            name="get_deficiency_details",
            description="Fetches all details about a given deficiency, including task and work order info",
            inputSchema={
                "type": "object",
                "properties": {
                    "deficiency_id": {
                        "type": "string",
                        "description": "The deficiency ID."
                    }
                },
                "required": ["deficiency_id"]
            }
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
        ),
        Tool(
            name="get_assets",
            description="Fetches all assets from a workspace.",
            inputSchema={
                "type": "object",
                "properties": {
                    "workspace_name": {
                        "type": "string",
                        "description": "The workspace name."
                    }
                },
                "required": ["workspace_name"]
            }
        ),

] #end tools


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_recent_logins":
        return await get_recent_logins(arguments["since_date"])
    elif name == "get_user_tasks":
        return await get_user_tasks(arguments["identifier"])
    elif name == "get_task_sample":
        return await get_task_sample(arguments.get("limit", 5))
    elif name == "get_all_assigned_users":
        return await get_all_assigned_users()
    elif name == "get_overdue_tasks":
        return await get_overdue_tasks()
    elif name == "get_task_summary_report":
        return await get_task_summary_report()
    elif name == "get_task_assignee":
        return await get_task_assignee(arguments["workspace_name"])
    elif name == "get_activity_feed":
        return await get_activity_feed(arguments["workspace_name"])
    elif name == "get_workspace_forms":
        return await get_workspace_forms_tool(arguments["workspace_name"])
    elif name == "get_workspace_deficiencies":
        return await get_asset_deficiencies(arguments["workspace_name"])
    elif name == "get_work_orders":
        status = arguments.get("status")
        return await get_work_orders(status=status)
    elif name == "get_deficiency_details":
        return await get_deficiency_details(arguments["deficiency_id"])
    elif name == "get_assets":
        return await get_assets(arguments["workspace_name"])
    elif name == "get_team_tasks":
        return await get_team_tasks(arguments["team_name"])






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
