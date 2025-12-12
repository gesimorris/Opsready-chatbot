# Import modules
import os
import sys
from typing import List, Optional
from dotenv import load_dotenv
from mcp.types import TextContent
from opsready import get_tgt, get_st, get_api_session, get_csrf_token

load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

# Function to get work orders with optional filters
async def get_work_orders(workspace: Optional[str] = None, status: Optional[str] = None) -> List[TextContent]:

    try:
        print("\n==============================", file=sys.stderr, flush=True)
        print("get_work_orders CALLED", file=sys.stderr, flush=True)
        print("Workspace filter:", workspace, "Status filter:", status, file=sys.stderr, flush=True)
        print("==============================", file=sys.stderr, flush=True)

        # Step 1: CAS Auth
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            return [TextContent(type="text", text="Failed to obtain TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        if not st:
            return [TextContent(type="text", text="Failed to obtain ST")]

        session = get_api_session(st)

        csrf = get_csrf_token(session)
        if not csrf:
            return [TextContent(type="text", text="Failed to retrieve CSRF token")]

        # Step 2: Query Work Orders
        flex_id = "02bc2322-0998-4558-80f0-ddacaca51366"  # Work Orders table
        query_url = f"{BASE_URL}/api/table/{flex_id}/query"

        payload = {"references": True, "limit": 50, "offset": 0}    # Base payload

        # FILTERS
        
        filters = []

        if status:
            filters.append({
                "$type": "string",
                "operator": "equal",
                "left": {"$type": "field", "field": "cd7a0237-423c-4529-8d26-ee250775f976"},
                "right": {"$type": "string", "value": status.capitalize()}
            })

        if filters:
            payload["filter"] = filters[0]


        # Make POST request to query work orders
        headers = {"X-CSRF-Token": csrf, "Content-Type": "application/json"}
        resp = session.post(query_url, json=payload, headers=headers)

        # show api response (Using to debug)
        print("RAW RESPONSE:", resp.text, file=sys.stderr, flush=True) 

        resp.raise_for_status()

        # Parse response
        data = resp.json()
        results = data.get("results", [])

        if not results:
            return [TextContent(type="text", text="No work orders found.")]

        # Format output
        output = []
        for record in results:
            fields = record.get("fields", {})
            #for fid, val in fields.items():    Using to debug field ids
               # print(f"Field ID: {fid} => Value: {val}")

            wo = fields.get("e66e72ce-4624-4108-b509-61568a041dd9", {}).get("value", "N/A")     # This returns the work order number
            asset = fields.get("48815d21-077d-4cef-b02e-de0c3acb8a89", {}).get("value", "N/A")  # This returns the asset name
            workspace_val = asset.split(" - ")[0] if asset else "N/A"       # This uses the asset field to get workspace name
            status_val = fields.get("cd7a0237-423c-4529-8d26-ee250775f976", {}).get("value", "N/A") # This gets status
            desc = fields.get("fc164b66-e244-4b8f-8c79-f189738d8963", {}).get("value", "N/A")       # This gets description
            asset_type = fields.get("1c159c89-b20f-4632-b20f-6e81fcd25aec", {}).get("value", "N/A")  # This gets asset type
            time_made = fields.get("1c5a6805-6056-4f2e-9e18-f27e0dc71b2c", {}).get("value", "N/A")  # This gets time and date created
            engine_hours = fields.get("c6e44e25-6dd5-441e-bd2b-f7140f181874", {}).get("value", "N/A")   # This gets engine hours
            odometer_reading = fields.get("2fed0a51-a2ec-4178-92e7-c8edf826aaeb", {}).get("value", "N/A")   # This gets odometer reading
            total_hours = fields.get("a10f1667-0453-4b33-b7f0-d846744c7a3e", {}).get("value", "N/A")    # This gets total hours
            material_cost = fields.get("551cae39-4d68-4a40-b0cf-bbad882f4b5d", {}).get("value", "N/A")  # This gets material cost
            labor_cost = fields.get("fea802be-5bf2-4c14-83d6-530970b0a664", {}).get("value", "N/A")      # This gets labor cost
            date_changed = fields.get("4270ed59-2683-4bd8-bd5a-01b419cf14cb", {}).get("value", "N/A")   # This gets last date changed

            # Construct message to be returned
            msg = (
                f"Work Order: {wo}\n"
                f"Workspace: {workspace_val}\n"
                f"Status: {status_val}\n"
                f"Description: {desc}\n"
                f"Asset: {asset}\n"
                f"Type: {asset_type}\n"
                f"Date Created: {time_made}\n"
                f"Engine Hours: {engine_hours}\n"
                f"Odometer Reading: {odometer_reading}\n"
                f"Total Hours: {total_hours}\n"
                f"Total Cost of Materials: {material_cost}\n"
                f"Total Cost of Labor: {labor_cost}\n"
                f"Last Date Changed: {date_changed}\n"
                "---------------------------------------"
            )

            output.append(TextContent(type="text", text=msg))

        return output

    except Exception as e: 
        return [TextContent(type="text", text=f"Error: {e}")]
