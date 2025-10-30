# tools/tool_get_overdue_tasks.py

from mcp.types import TextContent
from typing import List
import os
from dotenv import load_dotenv
from datetime import datetime, timezone
from Unused.opsready import get_tgt, get_st, get_api_session

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://or-student-sandbox.opsready.com")
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")


async def get_overdue_tasks() -> List[TextContent]:
    """
    Return all tasks whose due_date is before today's UTC date.
    """

    try:
        # --- Authenticate (same CAS flow as other tools) ---
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            return [TextContent(type="text", text="Failed to obtain TGT (check .env).")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        if not st:
            return [TextContent(type="text", text="Failed to obtain ST for /api/login service.")]

        session = get_api_session(st)
        resp = session.get(f"{BASE_URL}/api/task?limit=500&offset=0")
        if resp.status_code == 401:
            # Retry once
            st = get_st(tgt, service_url)
            session = get_api_session(st)
            resp = session.get(f"{BASE_URL}/api/task?limit=500&offset=0")

        resp.raise_for_status()
        tasks = resp.json()

    except Exception as e:
        return [TextContent(type="text", text=f"Authentication or fetch error: {e}")]

    if not tasks:
        return [TextContent(type="text", text="No tasks found in the system.")]

    # --- unwrap payload if wrapped ---
    if isinstance(tasks, dict):
        for key in ("items", "results", "data", "tasks"):
            if key in tasks and isinstance(tasks[key], list):
                tasks = tasks[key]
                break

    now = datetime.now(timezone.utc)
    overdue = []

    for t in tasks:
        due_raw = t.get("due_date") or t.get("due")
        if not due_raw:
            continue
        try:
            due = datetime.fromisoformat(due_raw.replace("Z", "+00:00"))
            if due < now:
                overdue.append(t)
        except Exception:
            continue

    if not overdue:
        return [TextContent(type="text", text="No overdue tasks found.")]

    lines = [f"Overdue tasks as of {now.strftime('%Y-%m-%d %H:%M UTC')}:"]

    for t in overdue:
        title = t.get("title", "<Untitled Task>")
        assigned = t.get("assigned_to", {})
        if isinstance(assigned, dict):
            assigned = assigned.get("name") or assigned.get("username") or "Unassigned"
        due = t.get("due_date") or t.get("due") or "N/A"
        lines.append(f"- {title} | Assigned: {assigned} | Due: {due}")

    lines.append(f"\nTotal overdue: {len(overdue)}")
    return [TextContent(type="text", text="\n".join(lines))]
