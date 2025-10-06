import os
from dotenv import load_dotenv
import requests
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP

load_dotenv()
mcp = FastMCP("opsready")
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")
'''
def get_tgt(username: str, password: str) -> Optional[str]:
    url = f"{BASE_URL}/cas/v1/tickets"
    data = {"username": username, "password": password}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        tgt = response.json().get("tgt")
        return tgt
    except requests.exceptions.RequestException as e:
        print("Failed to get TGT", e)
        return None

def get_st(tgt: str, service: str) -> Optional[str]:
    url = f"{BASE_URL}/cas/v1/tickets/{tgt}"
    params = {"service": service}
    try:
        response = requests.post(url, json=params)
        response.raise_for_status()
        st = response.json().get("st")
        return st
    except requests.exceptions.RequestException as e:
        print("Failed to get ST", e)
        return None


def get_workspace(st: str) -> Optional[Dict]:
    url = f"{BASE_URL}/api/workspace"
    headers = {"Authorization": f"? {st}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            print("Response not JSON:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print("Failed to get workspace", e)
        return None

@mcp.tool()
async def get_workspace_tool() ->str:
    data = get_workspace()
    if not data:
        return "Failed to get workspace"

    workspace_list = [f"{w.get('id', '?')}: {w.get('name', '?')}" for w in data.get("workspaces", [])]
    return "\n".join(workspace_list) if workspace_list else "No workspaces found."


if __name__ == "__main__":
    #mcp.run(transport='stdio')
    import asy


'''
load_dotenv()

#working
def get_tgt(username: str, password: str) -> Optional[str]:
    url = f"{BASE_URL}/cas/v1/tickets"
    headers = { "Content-Type": "application/x-www-form-urlencoded","Accept": "application/json" }
    data = {"username": username, "password": password}
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        tgt_url = response.text.strip()
        tgt = tgt_url.split("/")[-1]
        return tgt

    except requests.exceptions.RequestException as e:
        print("Failed to get TGT", e)
        return None
#working
def get_st(tgt: str, service: str) -> Optional[str]:
    url = f"{BASE_URL}/cas/v1/tickets/{tgt}"
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    data = {"service": service}
    try:
        response = requests.post(url, data=data, headers=headers)
        response.raise_for_status()
        st=response.text.strip()
        return st

    except requests.exceptions.RequestException as e:
        print("Failed to get ST", e)
        return None



#develop api session next


#throws not allowed for url error
def get_workspace(st: str) -> Optional[Dict]:
    url = f"{BASE_URL}/api/workspace"
    headers = {"Authorization": f"? {st}"}
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        try:
            return response.json()
        except ValueError:
            print("Response not JSON:", response.text)
            return None
    except requests.exceptions.RequestException as e:
        print("Failed to get workspace", e)
        return None




if __name__ == "__main__":
    tgt = get_tgt(USERNAME, PASSWORD)
    if not tgt:
        exit("Cannot continue without a TGT")

    st=get_st(tgt,f"{BASE_URL}/api/workspaces")
    if not st:
        exit("Cannot continue without a ST")

    workspaces = get_workspace(st)
    if workspaces:
        print("Workspaces fetched successfully:")
        print(workspaces)
    else:
        print("Failed to fetch workspaces.")








