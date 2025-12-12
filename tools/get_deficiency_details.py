import os
from typing import List
from dotenv import load_dotenv
from mcp.types import TextContent
from opsready import get_tgt, get_st, get_api_session


load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

async def get_deficiency_details(deficiency_id: str) -> List[TextContent]:
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

        deficiency_url = f"{BASE_URL}/api/table/{flex_id}/{deficiency_id}"

        # with flex id, can get the results based on the query below
        table_url = f"{BASE_URL}/api/table/{flex_id}/query"
        table_response = session.get(table_url)
        table_data = table_response.json()

        # query that gets the tasks where the field "e00..." (workspace) is workspace_id
        query = {
            "filter": {
                "$type": "string",
                "operator": "equal",
                "left": {"$type": "field", "field": "1fc8d85e-8098-4ab7-a332-22cca9fdab2f"},
                "right": {"$type": "string", "value": deficiency_id}
            }
        }
        query_w = {
            "filter": {
                "$type": "id",
                "operator": "equal",
                "left": {"$type": "field", "field": "1fc8d85e-8098-4ab7-a332-22cca9fdab2f"},
                "right": {"$type": "id", "value": deficiency_id}
            }
        }

        # get the results
        query_response = session.post(table_url, json=query)
        query_response.raise_for_status()
        results = query_response.json()

        res = results.get("results", [])
        if not res:
            return [TextContent(type="text", text="No deficiencies found")]
        deficiency_details = res[0]

        task_id = deficiency_details["fields"].get("fb1198c1-25c7-4690-acfa-bb99d3fbcee9",{}).get('value')

        tasks_url = f"{BASE_URL}/api/task/{task_id}"

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

            if assignee:
                assignee_name = user_map.get(assignee, "Unknown User")
                lines.append(f"{title} is due {due_date} and assigned to {assignee_name}")
            else:
                lines.append(f"{title} is due {due_date} unassigned")

        if lines:
            return [TextContent(type="text", text="\n".join(lines))]

    except Exception as e:
        return [TextContent(type="text", text=f"Error: {e}")]








