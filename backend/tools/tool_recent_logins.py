"""
Tool that takes a query like "Who has all signed in since 2025-05-01"
Returns all the users that signed in to the site, how many times, and the time

"""
from datetime import datetime, timezone
import os
from dotenv import load_dotenv
from mcp.types import TextContent
from backend.opsready import get_tgt, get_st, get_api_session


load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

async def get_recent_logins(since_date: str) -> list[TextContent]:

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

