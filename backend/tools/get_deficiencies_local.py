"""
******************************
Working rn locally to return the deficiencies text, needed to update the api session
function to get csrf too, need to implement this into claude
******************************
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
from mcp.types import TextContent
import os
from dotenv import load_dotenv
import requests
from typing import Any, Dict, Optional
from mcp.server.fastmcp import FastMCP
from pprint import pprint


load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")
workspace_name = "Summit Base"

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

tgt = get_tgt(USERNAME, PASSWORD)
service_url = f"{BASE_URL}/api/login"
st = get_st(tgt, service_url)
session = get_api_session(st)






# Get form access,
form_access_id = "ead8e438-129c-4f6f-a440-6280021d9762" #defecincies form id
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
        "$type": "composite",
        "operator": "all",
        "filters": [
            {
                "$type": "string",
                "operator": "equal",
                "left": {"$type": "field", "field": "f5f5d9a8-c180-4ada-a1bc-055c87eb5365"},
                "right": {"$type": "task", "value": "Unresolved"}
            },
            {
                "$type": "boolean",
                "operator": "equal",
                "left": {"$type": "archived"},
                "right": {"$type": "boolean", "value": False}
            }

        ]
    }
}
results = session.post(table_url, json=query_body)

#print(output)
print("flex_id:", flex_id)
print("table_url:", table_url)
print(results.status_code)
for f in table_data["fields"]:
    print(f["id"], f.get("system_alias"), f["$type"])
pprint(results.text)
#pprint(table_data)





