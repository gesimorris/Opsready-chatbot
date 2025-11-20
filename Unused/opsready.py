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



#recently works to get tgt and st not session
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
'''
**Uncomment for last working**
def get_api_session(st):
    url = f"{BASE_URL}/api/login?ticket={st}"
    print(f"\n=== Login Request ===")
    print(f"URL: {url}")

    session = requests.Session()
    response = session.get(url)

    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body: {response.text[:500]}")
    print(f"Session Cookies: {session.cookies.get_dict()}")
    print(f"===================\n")

    response.raise_for_status()
    return session
'''
def get_api_session(st):
    session = requests.Session()
    url = f"{BASE_URL}/api/login?ticket={st}"
    login_response = session.get(url)
    login_response.raise_for_status()


    csrf_url = f"{BASE_URL}/api/csrf_token"
    csrf_response = session.get(csrf_url)
    csrf_response.raise_for_status()


    csrf_token = csrf_response.headers.get("x-csrf-token")
    if not csrf_token:
        raise Exception("CSRF token not found in headers")

    # Add token to session headers for future requests
    session.headers.update({"X-CSRF-Token": csrf_token})
    return session



#throws not allowed for url error
def get_workspace(session: requests.Session) -> Optional[Dict]:
    url = f"{BASE_URL}/api/workspace?limit=1000"
    #headers = {"Authorization": f"? {st}"}

    print(f"\n=== Workspace Request ===")
    print(f"URL: {url}")
    print(f"Session Cookies: {session.cookies.get_dict()}")

    try:
        response = session.get(url)
        response.raise_for_status()

        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text[:500]}")
        print(f"========================\n")

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
    print(tgt)
    if not tgt:
        exit("Cannot continue without a TGT")

    #st=get_st(tgt,f"{BASE_URL}/api/workspace")
    service_url = f"{BASE_URL}/api/login"  # Changed from /workspaces to /workspace
    st = get_st(tgt, service_url)
    print(st)
    if not st:
        exit("Cannot continue without a ST")
    session = get_api_session(st)

    workspaces = get_workspace(session)
    if workspaces:
        print("Workspaces fetched successfully:")
        print(workspaces)
    else:
        print("Failed to fetch workspaces.")









