
import os
from typing import List, Optional
from dotenv import load_dotenv
from mcp.types import TextContent
from Unused.opsready import get_tgt, get_st, get_api_session

"""
Working, need to add way to map creator_id to actual users name


"""

load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

async def get_task_assignee(workspace_name: str, unassigned_only: Optional[bool] = False) -> List[TextContent]:
    all_ws_url = f"{BASE_URL}/api/workspace?limit=50&offset=0&archived=false&order=_created,desc,,last&hidden=false"

    try:
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            print("failed to get TGT")
            return [TextContent(type="text", text="Failed to get TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        session = get_api_session(st)

        response = session.get(all_ws_url)
        response.raise_for_status()
        data = response.json()

        workspace_id= None
        for ws in data:
            if ws.get("name", "").lower() == workspace_name.lower():
                workspace_id = ws.get("id")
                break
        if not workspace_id:
            return [TextContent(type="text", text="Failed to get workspace with that name")]

        tasks_url = (f"{BASE_URL}/api/task/flat?limit=100&offset=0&order=due_date,asc,false,last&order=priority,"
                     f"asc&order=title,asc&include_references=true&priorities=EMERGENCY&priorities=PRIORITY"
                     f"&priorities=ROUTINE&priorities=NONE&states=OPEN&workspace_id={workspace_id}")

        tasks_response = session.get(tasks_url)
        tasks_response.raise_for_status()
        tasks = tasks_response.json()

        if not tasks:
            return [TextContent(type="text", text="Failed to get tasks")]

        tasks_list = tasks.get("results", [])
        references = tasks.get("references", {})
        accounts = references.get("accounts", {})


        user_map = {acc_id: acc_data.get("name") for acc_id, acc_data in accounts.items()}

        lines = []
        for task in tasks_list:
            title = task.get("title", "")
            due_date = task.get("due_date", "")
            priority = task.get("priority", "")
            assignee = task.get("assignee_id", "")

            if unassigned_only and assignee:
                continue

            if assignee:
                assignee_name = user_map.get(assignee, "Unknown User")
                lines.append(f"{title} is due {due_date} and assigned to {assignee_name}")
            else:
                lines.append(f"{title} is due {due_date} unassigned")

        if not lines:
            msg = "All tasks are assigned." if unassigned_only else "No tasks found in workspace."
            return [TextContent(type="text", text=msg)]

        label = "Unassigned tasks" if unassigned_only else "All tasks"
        output = f"**{label} in {workspace_name}:**\n" + "\n".join(lines)
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]



