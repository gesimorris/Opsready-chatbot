from datetime import datetime, timezone
import os
from typing import List

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

async def get_activity_feed(workspace_name: str) -> List[TextContent]:
#url to get all the workstations
    all_ws_url = f"{BASE_URL}/api/workspace?limit=50&offset=0&archived=false&order=_created,desc,,last&hidden=false"

#authenticate
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


        #get the activity for the user requested workspace
        activity_feed_url = (
            f"{BASE_URL}/api/workspace/{workspace_id}/events/flat"
            "?limit=50&offset=0&include_references=true"
            "&categories=chat&categories=data&categories=details"
        )

        activity_response = session.get(activity_feed_url)
        activity_response.raise_for_status()
        data = activity_response.json()

        if not data:
            return [TextContent(type="text", text="No recent activities found for workspace")]

        activities_list = data.get("results", [])
        references = data.get("references", {})
        accounts = references.get("accounts", {})
        accounts_list = data.get("accounts", [])
        forms = data.get("forms", [])

        user_map = {acc_id: acc_data.get("name") for acc_id, acc_data in accounts.items()}




        '''users_name_url = f"{BASE_URL}/api/workspace/{workspace_id}/accounts?access_type=all"
        users_response = session.get(users_name_url)
        users_response.raise_for_status()
        users_data = users_response.json()'''

        #user_list = users_data.get("results", [])

        '''user_map = {}
        for u in users_data.get("results", []):
            user_map[u.get("id")] = u.get("name")'''


        lines = []
        for d in activities_list[:10]:
            created = d.get("created")
            creator_id = d.get("creator_id")
            content = d.get("content")
            form_id = d.get("form_id")

            creator_name = user_map.get(creator_id, creator_id)
            lines.append(f" {created} — {creator_name} - {content}")



        output = f"Recent activity in **{workspace_name}**:\n" + "\n".join(lines)
        return [TextContent(type="text", text=output)]





    except Exception as e:
        return [TextContent(type="text", text=f" Error: {e}")]

    #get workspace name from input -> map it to ID store ID in var,
    #pass that var to call the activity feed




