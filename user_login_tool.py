from datetime import datetime, timezone
from typing import List
import os
from dotenv import load_dotenv
import requests
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
import requests
import asyncio
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent
from opsready import get_tgt, get_st, get_api_session

"""Logic works, tested in test_user_logins, can auth and get users. Next steps for this file is to set up claude desktop and
point it to server to test that works."""
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
                        users.append(user.get("id"))
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


async def main():
    """Run the MCP server using stdio transport."""
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())





