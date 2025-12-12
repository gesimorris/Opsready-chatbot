"""
Tool to display the activity feed on the given workspace
Takes query "Show me the activity in Summit Base"
Returns the activity in that workspace, forms submitted, incidents submitted etc
"""
import os
from typing import List

from dotenv import load_dotenv
from mcp.types import TextContent
from opsready import get_tgt, get_st, get_api_session

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
# end auth
        #get sessions and get workstations
        response = session.get(all_ws_url)
        response.raise_for_status()
        data = response.json()

#loop through all the ws gotten from above, find the is that matches the param, store in val
        workspace_id= None
        for ws in data:
            if ws.get("name", "").lower() == workspace_name.lower():
                workspace_id = ws.get("id")
                break
        if not workspace_id:
            return [TextContent(type="text", text="Failed to get workspace with that name")]


#get the activity feed for the user requested workspace sent through param
        activity_feed_url = (
            f"{BASE_URL}/api/workspace/{workspace_id}/events/flat"
            "?limit=50&offset=0&include_references=true"
            "&categories=chat&categories=data&categories=details"
        )

#get response data from the activity feed api
        activity_response = session.get(activity_feed_url)
        activity_response.raise_for_status()
        data = activity_response.json()

#if not data, meaning no workspace with that name entered
        if not data:
            return [TextContent(type="text", text="No recent activities found for workspace")]

#get specific responses that we want and store them in variables
        activities_list = data.get("results", [])
        references = data.get("references", {})
        accounts = references.get("accounts", {})
        accounts_list = data.get("accounts", [])
        forms = references.get("forms", {})

        #map
        user_map = {acc_id: acc_data.get("name") for acc_id, acc_data in accounts.items()}
        form_map = {form_id: form_data.get("name") for form_id, form_data in forms.items()}


        lines = []
        for d in activities_list[:10]:
            created = d.get("created")
            creator_id = d.get("creator_id")
            content = d.get("content")
            form_id = d.get("form_id")
            feature_action = d.get("feature_action")

            creator_name = user_map.get(creator_id, creator_id)

            form_name = form_map.get(form_id, "Unknown Form")


            if not content and form_id:
                if feature_action == "EDIT":
                    content = f"edited a form submission ({form_name})"
                elif feature_action == "CREATE":
                    content = f"created a new form submission ({form_name})"
                else:
                    content = f"updated form submission ({form_name})"

            lines.append(f" {created} — {creator_name} - {content or 'None'}")


#create output string to send to claude
        output = f"Recent activity in **{workspace_name}**:\n" + "\n".join(lines)
        return [TextContent(type="text", text=output)]

    except Exception as e:
        return [TextContent(type="text", text=f" Error: {e}")]





