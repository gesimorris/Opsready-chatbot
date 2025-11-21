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

        #forms_url = (f"{BASE_URL}api/workspace/{workspace_id}/form?offset=0&limit=500&name=")

        #forms_response = session.get(forms_url)
        #forms_response.raise_for_status()
        #forms= forms_response.json()

        #if not forms:
           # return [TextContent(type="text", text="Failed to get forms with that name")]
        form_access_id = "7f08e35a-9f0b-45ff-a554-7caff337f664"  # defecincies form id
        access_url = f"{BASE_URL}/api/form/access/{form_access_id}"
        access_data = session.get(access_url).json()
        template_id = access_data.get("template_id")

        # Get form template
        template_data = session.get(f"{BASE_URL}/api/form/template/{template_id}").json()
        flex_id = template_data.get("flex_definition_id")

        table = f"{BASE_URL}/api/table/{flex_id}"
        table_response = session.get(table)
        table_data = table_response.json()
        table_url = f"{BASE_URL}/api/table/{flex_id}/query"

        query_body = {
            "filter": {
                "$type": "id",
                "operator": "equal",
                "left": {"$type": "field", "field": "e00df19"},
                "right": {"$type": "id", "value": workspace_id}  # workspace_id from workspace mapping
            },
            "limit": 100,
            "offset": 0
        }

        results = session.post(table_url, json=query_body)

        lines = []
        for i, record in enumerate(results, start=1):
            fields = record.get("fields", {})

            deficiency = fields.get("7483694f-7f64-4dbc-9e10-a738ad9ad1e7", {}).get("value", "Unknown Deficiency")
            status = fields.get("dc68de1b-8104-449b-8334-41c28e0e4c4d", {}).get("value", "Unknown Status")

            lines.append(f"{i}. {deficiency} — {status}")

        output = f"**Deficiencies in {workspace_name}:**\n" + "\n".join(lines)
        print(output)
        



    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]