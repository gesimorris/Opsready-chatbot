# tools/tool_debug_tasks_sample.py

from mcp.types import TextContent
from typing import List
import os
from dotenv import load_dotenv
from Unused.opsready import get_tgt, get_st, get_api_session

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://or-student-sandbox.opsready.com")
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")


async def get_task_sample(limit: int = 5) -> List[TextContent]:
    """
    Fetches a small sample of tasks from OpsReady to inspect structure.
    Returns the first few tasks with key fields for debugging.
    """

    try:
        # Step 1: Authenticate (same CAS flow as your working tools)
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            return [TextContent(type="text", text="Failed to get TGT (check .env).")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        if not st:
            return [TextContent(type="text", text="Failed to get ST for /api/login.")]

        session = get_api_session(st)

        # Step 2: Fetch tasks
        resp = session.get(f"{BASE_URL}/api/task?limit={limit}&offset=0")
        if resp.status_code == 401:
            # Retry once if session cookie expired
            st = get_st(tgt, service_url)
            session = get_api_session(st)
            resp = session.get(f"{BASE_URL}/api/task?limit={limit}&offset=0")

        resp.raise_for_status()
        data = resp.json()

    except Exception as e:
        return [TextContent(type="text", text=f"Error fetching tasks: {e}")]

    # Step 3: Normalize payload
    tasks = data
    if isinstance(tasks, dict):
        for key in ("items", "results", "data", "tasks"):
            if key in tasks and isinstance(tasks[key], list):
                tasks = tasks[key]
                break

    if not tasks:
        return [TextContent(type="text", text="No tasks found in the system.")]

    # Step 4: Build readable summary
    lines = [f"Showing up to {limit} tasks (out of {len(tasks)} available):"]
    for i, t in enumerate(tasks[:limit]):
        title = t.get("title", "<Untitled Task>")
        assigned = (
            t.get("assigned_to")
            or t.get("assignee")
            or t.get("assigned_user")
            or t.get("assignedUser")
            or t.get("assignees")
            or "N/A"
        )
        status = t.get("status", "N/A")
        due = t.get("due_date") or t.get("due") or "N/A"
        lines.append(f"{i+1}. {title}\n   Assigned: {assigned}\n   Status: {status}\n   Due: {due}\n")

    return [TextContent(type="text", text="\n".join(lines))]
