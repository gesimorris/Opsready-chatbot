import os
from typing import List
from dotenv import load_dotenv
from mcp.types import TextContent
from backend.opsready import get_tgt, get_st, get_api_session

load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

async def get_assets(workspace_name: str ) -> List[TextContent]:
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
        form_access_id = "7f08e35a-9f0b-45ff-a554-7caff337f664"
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

        table_url = f"{BASE_URL}/api/table/{flex_id}/query"
        table_response = session.get(table_url)
        table_data = table_response.json()
        workspace = "SUMMIT_BASE"

        query = {
            "filter": {
                "$type": "string",
                "operator": "equal",
                "left": {"$type": "field", "field": "e3896d69-b2f0-433d-9766-6603d30e133a"},
                "right": {"$type": "string", "value": workspace}
            }
        }

        # get the results
        query_response = session.post(table_url, json=query)
        query_response.raise_for_status()
        results = query_response.json()

        res = results.get("results", [])
        if not res:
            return [TextContent(type="text", text="No assets found")]

        # loop through results, get the def name and status
            # loop through results, get the def name and status
        assets_output = []
        for i, record in enumerate(res, start=1):
            fields = record.get("fields", {})
            asset_name = fields.get("7b5d58f6-9d54-4562-82e3-b1371c3d7be2", {}).get("value", "Unknown Asset")
            asset_id = fields.get("3aa5fd57-c501-4b7c-918c-015ae09d788f", {}).get("value", "Unknown ID")
            deficiency_link = fields.get("4145d904-e7fb-419d-94bf-a75d45b25d8b", {}).get("value", "Unknown Link")
            deficiency_id = None

            if deficiency_link and isinstance(deficiency_link, str):
                deficiency_id = deficiency_link.rstrip("/").split("/")[-1]
            assets_output.append(f"{i}. {asset_id} — {asset_name} - {deficiency_id}")


        output = f"**Deficiencies in {workspace_name}:**\n" + "\n".join(assets_output)
        return [TextContent(type="text", text=output)]
        #return [TextContent(type="json", text=json.dumps(assets_output, indent=2))]


    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]