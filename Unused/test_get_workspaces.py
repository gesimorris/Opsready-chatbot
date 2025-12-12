import json
from typing import Dict, List
from opsready import get_tgt, get_st, get_api_session
import os
from dotenv import load_dotenv

load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")


def get_specific_workspace(workspace_name: str):
    try:
        name = workspace_name.strip().lower()
    except ValueError:
        print("Invalid workspace name.")
        return

    tgt = get_tgt(USERNAME, PASSWORD)
    if not tgt:
        print("Failed to get TGT.")
        return

    service_url = f"{BASE_URL}/api/login"
    st = get_st(tgt, service_url)
    if not st:
        print("Failed to get ST.")
        return

    session = get_api_session(st)

    url = f"{BASE_URL}/api/workspace?limit=50&offset=0&archived=false&order=_created,desc,,last&hidden=false"
    response = session.get(url)
    response.raise_for_status()
    data = response.json()

    # Create a list of workspaces
    workspaces_list: List[Dict] = data
    name_to_find = workspace_name.strip().lower()  # Normalize the input name

    # List to hold matching workspaces
    matching_workspaces = [
        ws for ws in workspaces_list  # List comprehension to filter workspaces
        if ws.get("name") and name_to_find in ws.get("name").strip().lower()  # Case-insensitive match
    ]

    # Print the results
    if matching_workspaces:
        print(f"\n*** Found {len(matching_workspaces)} Workspaces matching '{workspace_name}' ***")

        return matching_workspaces
    else:
        print(f"\nNo workspaces found matching '{workspace_name}'.")
        return []


if __name__ == "__main__":
    workspace_name = input("Enter the workspace name to search for: ")
    results = get_specific_workspace(workspace_name)
    if results:
        print(json.dumps(results, indent=4))