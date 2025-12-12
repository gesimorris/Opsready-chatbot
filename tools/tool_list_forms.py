import requests
from typing import Dict, List, Optional
import os
from dotenv import load_dotenv
from mcp.types import TextContent  # Assuming mcp.types is available for this environment
# Ensure this import path matches your project structure:
from opsready import get_tgt, get_st, get_api_session

"""
This file is a tool called get_workspace_forms, it has a function 
get_workspace_forms_tool that takes in the parameter workspace_name. 
This file contains the logic to authenticate, find a workspace, and 
return a list of its available forms. THE API URL FOR ACCESSING THE ASSETS USES /MAPS AND DOES NOT WORK.
"""

# --- CONFIGURATION ---
load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

# --- INTERNAL HELPER FUNCTIONS ---

def _find_workspace(session: requests.Session, workspace_name: str) -> Optional[Dict]:
    """Internal function to find the target workspace using the active session."""
    url = f"{BASE_URL}/api/workspace?limit=50&offset=0&archived=false&order=_created,desc,,last&hidden=false"

    try:
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
    except requests.exceptions.RequestException:
        return None

    workspaces_list: List[Dict] = data
    name_to_find = workspace_name.strip().lower()

    # Find the first matching workspace
    matching_workspaces = [
        ws for ws in workspaces_list
        if ws.get("name") and name_to_find in ws.get("name").strip().lower()
    ]

    return matching_workspaces[0] if matching_workspaces else None

def _fetch_forms(session: requests.Session, workspace_id: str) -> List[Dict]:
    """Internal function to fetch the forms list for a given workspace ID."""
    url = (
        f"{BASE_URL}/api/workspace/{workspace_id}/form"
        f"?offset=0&limit=500&name="
    )

    try:
        response = session.get(url)
        response.raise_for_status()

        forms_data = response.json()

        # Robustly check the response structure for the list of forms
        if isinstance(forms_data, dict) and 'results' in forms_data:
            forms_list = forms_data['results']
        elif isinstance(forms_data, dict) and 'forms' in forms_data:
            forms_list = forms_data['forms']
        elif isinstance(forms_data, list):
            forms_list = forms_data
        else:
            forms_list = []

        return forms_list

    except requests.exceptions.RequestException:
        return []


# --- MAIN ASYNCHRONOUS TOOL FUNCTION ---

async def get_workspace_forms_tool(workspace_name: str) -> list[TextContent]:
    """
    Finds a specific workspace by name, fetches its list of forms, and returns
    the results formatted as a list of TextContent objects.
    """

    if not workspace_name:
        return [TextContent(type="text", text="Workspace name cannot be empty.")]

    try:
        # 1. AUTHENTICATION
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            return [TextContent(type="text", text="Failed to get TGT. Check credentials.")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        if not st:
            return [TextContent(type="text", text="Failed to get ST during login process.")]

        session = get_api_session(st)

        # 2. FIND WORKSPACE
        target_workspace = _find_workspace(session, workspace_name)

        if not target_workspace:
            return [TextContent(type="text", text=f"No workspaces found matching '{workspace_name}'.")]

        workspace_id = target_workspace.get("id")
        workspace_display_name = target_workspace.get('name')

        # 3. FETCH FORMS
        forms_list = _fetch_forms(session, workspace_id)

        # 4. FORMAT OUTPUT
        if not forms_list:
            return [TextContent(type="text", text=f"No forms found for workspace '{workspace_display_name}'.")]

        formatted_forms = []
        asset_form_id = None

        for form in forms_list:
            form_name = form.get('name', 'N/A')
            form_id = form.get('id', 'N/A')

            # Check for asset list forms for easy identification
            if form_name != 'N/A' and ("asset list" in form_name.lower() or "asset" in form_name.lower()):
                asset_form_id = form_id
            else:
                formatted_forms.append(f"• {form_name} (ID: {form_id})")

        # Create a clean, multi-line string for the final output
        output_text = (
                + "\n".join(formatted_forms)
        )

        # Optionally add the Asset ID explicitly if found
        if asset_form_id:

            return [TextContent(type="text", text=output_text)]

    except Exception as e:
        # Catch any unexpected errors during the process
        return [TextContent(type="text", text=f"An error occurred during form retrieval: {str(e)}")]