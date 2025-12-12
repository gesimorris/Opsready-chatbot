# tools/tool_get_task_summary_report.py

from mcp.types import TextContent
from typing import List
import os
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from collections import Counter
from opsready import get_tgt, get_st, get_api_session

load_dotenv()

BASE_URL = os.getenv("BASE_URL", "https://or-student-sandbox.opsready.com")
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")


async def get_task_summary_report() -> List[TextContent]:
    """
    Produces a high-level summary of OpsReady tasks:
    - total, assigned, unassigned
    - overdue and due soon
    - most common categories (based on title keywords)
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

    # --- Step 3: unwrap payload if wrapped ---
    if isinstance(tasks, dict):
        for key in ("items", "results", "data", "tasks"):
            if key in tasks and isinstance(tasks[key], list):
                tasks = tasks[key]
                break

    # --- Step 4: compute metrics ---
    now = datetime.now(timezone.utc)
    due_soon_threshold = now + timedelta(days=7)

    total = len(tasks)
    assigned = 0
    unassigned = 0
    overdue = 0
    due_soon = 0
    categories = Counter()

    for t in tasks:
        # assignment
        a = t.get("assigned_to") or t.get("assignee")
        if a:
            assigned += 1
        else:
            unassigned += 1

        # due-date
        due_raw = t.get("due_date") or t.get("due")
        if due_raw:
            try:
                due = datetime.fromisoformat(due_raw.replace("Z", "+00:00"))
                if due < now:
                    overdue += 1
                elif due < due_soon_threshold:
                    due_soon += 1
            except Exception:
                pass

        # category from title keywords
        title = t.get("title", "").lower()
        for keyword in ["inspection", "report", "hazard", "incident", "operation", "follow-up", "check", "request"]:
            if keyword in title:
                categories[keyword] += 1

    # --- Step 5: format report ---
    lines = [
        f"📊 OpsReady Task Summary Report — {now.strftime('%Y-%m-%d %H:%M UTC')}\n",
        f"Total tasks: {total}",
        f"Assigned: {assigned}",
        f"Unassigned: {unassigned}",
        f"Overdue: {overdue}",
        f"Due soon (next 7 days): {due_soon}\n",
    ]

    if categories:
        lines.append("Top task categories:")
        for k, v in categories.most_common(10):
            lines.append(f"- {k.title()}: {v}")

    lines.append("\nKey insights:")
    if unassigned > assigned:
        lines.append("• Many tasks remain unassigned — consider reallocation.")
    if overdue > 0:
        lines.append("• There are overdue tasks requiring attention.")
    if due_soon > 0:
        lines.append("• Several tasks are approaching their due dates.")
    if not categories:
        lines.append("• Task titles don’t include recognizable category keywords.")

    lines.append("\n✅ Summary complete.")

    return [TextContent(type="text", text="\n".join(lines))]
