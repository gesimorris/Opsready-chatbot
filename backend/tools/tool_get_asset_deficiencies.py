"""
***************************************
Tool to get all the asset deficiencies that have been entered into forms by a user, from a specific workspace
Takes query "Show me the deficiencies in Summit Base"
Returns the deficiencies in that workspace

Expand:
- Deficiencies with no task assigned to them
- Deficiencies with no WO
***************************************
"""
import os
from typing import List
from dotenv import load_dotenv
from mcp.types import TextContent
from backend.opsready import get_tgt, get_st, get_api_session

load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

async def get_asset_deficiencies(workspace_name: str ) -> List[TextContent]:
    all_ws_url = f"{BASE_URL}/api/workspace?limit=50&offset=0&archived=false&order=_created,desc,,last&hidden=false"
#auth
    try:
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            print("failed to get TGT")
            return [TextContent(type="text", text="Failed to get TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        session = get_api_session(st)
#end auth

#get session and all ws
        response = session.get(all_ws_url)
        response.raise_for_status()
        data = response.json()
#loop through ws and store the id of passed ws in var
        workspace_id= None
        for ws in data:
            if ws.get("name", "").lower() == workspace_name.lower():
                workspace_id = ws.get("id")
                break
        if not workspace_id:
            return [TextContent(type="text", text="Failed to get workspace with that name")]


#deficiencies form id, get the template id, get the flex id
        form_access_id = "c27c33ba-75f8-432a-bd63-c4e361a52f67"
        access_url = f"{BASE_URL}/api/form/access/{form_access_id}"
        access_response = session.get(access_url)
        access_data = access_response.json()
        template_id = access_data.get("template_id")
        if not template_id:
            return [TextContent(type="text", text="Failed to get template with that id")]

        template_url = f"{BASE_URL}/api/form/template/{template_id}"
        template_response = session.get(template_url)
        template_data = template_response.json()
        flex_id = template_data.get("flex_definition_id")
        if not flex_id:
            return [TextContent(type="text", text="Failed to get flex with that id")]

#with flex id, can get the results based on the query below
        table_url = f"{BASE_URL}/api/table/{flex_id}/query"
        table_response = session.get(table_url)
        table_data = table_response.json()

#temp testing query, works
        query_body = {
            "filter": {
                "$type": "string",
                "operator": "equal",
                "left": {"$type": "field", "field": "dc68de1b-8104-449b-8334-41c28e0e4c4d"},
                "right": {"$type": "string", "value": "Unresolved"}
            }
        }
#query that gets the tasks where the field "e00..." (workspace) is workspace_id
        query =  {
            "filter": {
                "$type": "id",
                "operator": "equal",
                "left": {"$type": "field", "field": "e00dfdc2-7552-4760-a1eb-cde92f260819"},
                "right": {"$type": "id", "value": workspace_id}
            }
        }

#get the results
        query_response = session.post(table_url, json=query)
        query_response.raise_for_status()
        results = query_response.json()

        res = results.get("results", [])
        if not res:
            return [TextContent(type="text", text="No deficiencies found")]

#loop through results, get the def name and status
        lines = []
        for i, record in enumerate(res, start=1):
            fields = record.get("fields", {})
            deficiency = fields.get("7483694f-7f64-4dbc-9e10-a738ad9ad1e7", {}).get("value", "Unknown Deficiency")
            id = fields.get("1fc8d85e-8098-4ab7-a332-22cca9fdab2f", {}.get("value", "Unknown ID"))
            status = fields.get("dc68de1b-8104-449b-8334-41c28e0e4c4d", {}).get("value", "Unknown Status")
            lines.append(f"{i}. {deficiency} — {status} - {id}")

        output = f"**Deficiencies in {workspace_name}:**\n" + "\n".join(lines)
        return [TextContent(type="text", text=output)]


    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]