# tools/tool_get_all_assigned_users.py

from mcp.types import TextContent
from typing import List
import os
from dotenv import load_dotenv
from collections import Counter
from opsready import get_tgt, get_st, get_api_session

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://or-student-sandbox.opsready.com")
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")


async def get_all_assigned_users() -> List[TextContent]:
    """
    Returns a list of all users who have one or more tasks assigned to them,
    along with the count of tasks each user has.
    """

    try:
        # --- Step 1: Authenticate ---
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            return [TextContent(type="text", text="Failed to obtain TGT (check .env).")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        if not st:
            return [TextContent(type="text", text="Failed to obtain ST for /api/login service.")]

        session = get_api_session(st)

        # --- Step 2: Fetch all tasks ---
        resp = session.get(f"{BASE_URL}/api/task?limit=500&offset=0")
        if resp.status_code == 401:
            st = get_st(tgt, service_url)
            session = get_api_session(st)
            resp = session.get(f"{BASE_URL}/api/task?limit=500&offset=0")

        resp.raise_for_status()
        tasks = resp.json()

    except Exception as e:
        code = f" (HTTP {getattr(resp, 'status_code', '?')})" if 'resp' in locals() else ''
        return [TextContent(type="text", text=f"Failed to fetch tasks{code}: {e}")]

    if not tasks:
        return [TextContent(type="text", text="No tasks found in the system.")]

    # --- Step 3: Unwrap payload if needed ---
    if isinstance(tasks, dict):
        for key in ("items", "results", "data", "tasks"):
            if key in tasks and isinstance(tasks[key], list):
                tasks = tasks[key]
                break

    # --- Step 4: Extract assigned user names ---
    assignees = []
    for t in tasks:
        a = t.get("assigned_to") or t.get("assignee")
        if isinstance(a, dict):
            name = a.get("name") or a.get("username") or a.get("email")
            if name:
                assignees.append(name.strip())
        elif isinstance(a, str) and a.strip():
            assignees.append(a.strip())

    if not assignees:
        return [TextContent(type="text", text="No tasks have an assigned user field.")]

    # --- Step 5: Count how many tasks each user has ---
    counts = Counter(assignees).most_common()

    # --- Step 6: Format output ---
    lines = ["Users with assigned tasks:\n"]
    for name, count in counts:
        lines.append(f"- {name}: {count} task(s)")

    return [TextContent(type="text", text="\n".join(lines))]
