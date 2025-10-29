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

async def get_workspace_deficiencies(workspace_name: str) -> List[TextContent]:
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

        forms_url = (f"{BASE_URL}api/workspace/{workspace_id}/form?offset=0&limit=500&name=")

        forms_response = session.get(forms_url)
        forms_response.raise_for_status()
        forms= forms_response.json()

        if not forms:
            return [TextContent(type="text", text="Failed to get forms with that name")]


    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]