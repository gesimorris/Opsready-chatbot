# tools/tool_get_user_tasks.py

from mcp.types import TextContent
from typing import List
import os
from dotenv import load_dotenv
from opsready import get_tgt, get_st, get_api_session

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://or-student-sandbox.opsready.com")
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")


async def get_user_tasks(identifier: str) -> List[TextContent]:
    """
    Fetch all tasks assigned to a specific user.
    The identifier can be an email, username, or name (e.g. 'Adam Wilson').
    Uses the same CAS handshake as the working get_recent_logins tool.
    """

    if not identifier or not identifier.strip():
        return [TextContent(type="text", text="Please provide a user name, username, or email.")]

    query = identifier.lower().strip()

    # --- Auth: identical to get_recent_logins ---
    try:
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            return [TextContent(type="text", text="Failed to get TGT (check credentials in .env).")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        if not st:
            return [TextContent(type="text", text="Failed to get ST for /api/login service.")]

        # Establish the Session cookie internally
        session = get_api_session(st)

    except Exception as e:
        return [TextContent(type="text", text=f"Authentication error during CAS login: {e}")]

    # --- Fetch tasks with the authenticated session ---
    tasks_url = f"{BASE_URL}/api/task?limit=500&offset=0"

    try:
        resp = session.get(tasks_url)
        if resp.status_code == 401:
            # Retry once with a refreshed ST
            st = get_st(tgt, service_url)
            if not st:
                return [TextContent(type="text", text="401 Unauthorized and failed to refresh ST for /api/login.")]
            session = get_api_session(st)
            resp = session.get(tasks_url)

        resp.raise_for_status()
        tasks = resp.json()
    except Exception as e:
        code = f" (HTTP {getattr(resp, 'status_code', '?')})" if 'resp' in locals() else ''
        return [TextContent(type="text", text=f"Failed to fetch tasks{code}: {e}")]

    if not tasks:
        return [TextContent(type="text", text="No tasks found in the system.")]

    # --- Unwrap if the API responds with a wrapper ---
    if isinstance(tasks, dict):
        for key in ("items", "results", "data", "tasks"):
            if key in tasks and isinstance(tasks[key], list):
                tasks = tasks[key]
                break

    # --- Filter tasks for any match (email, username, or name) ---
    def matches_user(task: dict) -> bool:
        assigned = task.get("assigned_to") or task.get("assignee") or {}
        if isinstance(assigned, dict):
            for key in ("email", "username", "name"):
                val = assigned.get(key)
                if val and query in str(val).lower():
                    return True
        elif isinstance(assigned, str) and query in assigned.lower():
            return True
        return False

    user_tasks = [t for t in tasks if matches_user(t)]

    # --- Handle no matches ---
    if not user_tasks:
        total = len(tasks) if isinstance(tasks, list) else 0
        return [TextContent(
            type="text",
            text=f"No tasks found for '{identifier}'. (Fetched {total} tasks successfully; none matched that user.)"
        )]

    # --- Format nicely for Claude ---
    lines = [f"Tasks assigned to {identifier}:"]
    for t in user_tasks:
        title = t.get("title", "<Untitled Task>")
        status = t.get("status", "<No Status>")
        due = t.get("due_date") or t.get("due") or "N/A"
        assignee = t.get("assigned_to", {}).get("name") if isinstance(t.get("assigned_to"), dict) else t.get("assigned_to", "N/A")
        lines.append(f"- {title} | Assigned: {assignee} | Status: {status} | Due: {due}")

    return [TextContent(type="text", text="\n".join(lines))]
