from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from mcp.server import Server
from mcp.types import Tool, TextContent
from opsready import get_tgt, get_st, get_api_session
"""
*************************************************************************************************************************
FILE NOT IN USE ANYMORE, SERVER.PY IS MAIN SERVER, ALL TOOL LOGIC SHOULD BE DEFINED IN THEIR OWN SEPERATE FILE AND PLACED
IN "tools" DIRECTORY
*************************************************************************************************************************
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
                    "required": ["query_type"]
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_recent_logins":
        since_date = arguments["since_date"]

        try:
            since = datetime.strptime(since_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return [TextContent(
                type="text",
                text="Invalid date format. Use YYYY-MM-DD."
            )]

        url = f"{BASE_URL}/api/account?limit=500&offset=0&search=&with_teams=true"

        try:
            tgt = get_tgt(USERNAME, PASSWORD)
            if not tgt:
                print("failed to get TGT")
                return [TextContent(type="text", text="Failed to get TGT")]


            service_url = f"{BASE_URL}/api/login"
            st = get_st(tgt, service_url)
            session = get_api_session(st)
            response = session.get(url)
            response.raise_for_status()
            data = response.json()
        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Failed to fetch accounts: {str(e)}"
            )]

        users = []
        for user in data:
            last_login_str = user.get("last_login")
            if last_login_str:
                try:
                    last_login = datetime.fromisoformat(last_login_str.replace("Z", "+00:00"))
                    if last_login >= since:
                        users.append({
                            # "id": user.get("id"),
                            "name": user.get("username"),
                            "last_login": last_login_str
                        })
                except (ValueError, AttributeError):
                    continue

        if not users:
            return [TextContent(
                type="text",
                text=f"No users have logged in since {since_date}."
            )]

        return [TextContent(
            type="text",
            text=f"Users logged in since {since_date}: {', '.join(map(str, users))}"
        )]

    else:
        return [TextContent(
            type="text",
            text=f"Unknown tool: {name}"
        )]

'''
async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )'''
async def main():
    from mcp.server.stdio import stdio_server
    print("Server running")
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    import asyncio

    print("Starting OpsReady MCP Server...")
    asyncio.run(main())





