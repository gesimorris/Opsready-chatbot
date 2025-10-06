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

#working
def get_api_session(st: str) -> Optional[requests.Session]:
    url = f"{BASE_URL}/api/login?ticket={st}"
    headers = {"Authorization": f"? {st}"}
    try:
        session = requests.Session()
        response = session.get(url, headers=headers)
        response.raise_for_status()
        return session
    except requests.exceptions.RequestException as e:
        print("Failed to get API session", e)
        return None
    
# Exchanging ST for a session cookie (NOT WORKING NEEDED FOR WORKSPACE CALL)
def get_authenticated_session(service_url: str, st: str) -> requests.Session:
    session = requests.Session()
    response = session.get(f"{service_url}?ticket={st}")
    response.raise_for_status()
    return session

#throws not allowed for url error
def get_workspace(session: requests.Session) -> dict:
    url = f"{BASE_URL}/api/workspace"
    response = session.get(url)
    response.raise_for_status()
    return response.json()


# MAIN
if __name__ == "__main__":
    tgt = get_tgt(USERNAME, PASSWORD)
    if not tgt:
        print("Failed to obtain TGT")
        exit(1)
    print("TGT:", tgt)
    st = get_st(tgt, f"{BASE_URL}/api/login")
    if not st:
        print("Failed to obtain ST")
        exit(1)
    print("ST:", st)
    api_session = get_api_session(st)
    if not api_session:
        print("Failed to obtain API session")
        exit(1)
    print("API session: ", api_session)
    








