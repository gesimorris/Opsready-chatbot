import os
from typing import List, Optional
from dotenv import load_dotenv
from mcp.types import TextContent
from opsready import get_tgt, get_st, get_api_session


load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

async def get_team_tasks(team_name: str, unassigned_only: Optional[bool] = False) -> List[TextContent]:
    all_team_url = f"{BASE_URL}/api/team"


    try:
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            print("failed to get TGT")
            return [TextContent(type="text", text="Failed to get TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        session = get_api_session(st)

        response = session.get(all_team_url)
        response.raise_for_status()
        data = response.json()

        team_id= None
        for t in data:
            if t.get("name", "").lower() == team_name.lower():
                team_id = t.get("id")
                break
        if not team_id:
            return [TextContent(type="text", text="Failed to get workspace with that name")]

        get_tasks_in_team = f"{BASE_URL}/api/team/{team_id}/tasks?limit=100&offset=0&order=due_date,asc,false,last&order=priority,asc&order=title,asc&priorities=EMERGENCY&priorities=PRIORITY&priorities=ROUTINE&priorities=NONE&states=OPEN&states=BLOCKED&archived_workspaces=false"

        tasks_response = session.get(get_tasks_in_team)
        tasks_response.raise_for_status()
        tasks = tasks_response.json()
        tasks_list = tasks

        lines = []
        for task in tasks_list:
            title = task.get("title", "No Title")
            due_date = task.get("due_date", "No Due Date")
            priority = task.get("priority", "Unknown Priority")
            #assignee = task.get("assignee_id", "")

            lines.append(f"**{title}:** {due_date}")

        output = f"**in :**\n" + "\n".join(lines)
        return [TextContent(type="text", text=output)]

        if not tasks:
            return [TextContent(type="text", text="Failed to get tasks")]


    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]