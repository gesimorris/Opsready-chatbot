from datetime import datetime, timezone
from opsready import get_tgt, get_st, get_api_session
import os
from dotenv import load_dotenv
import requests

load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")

"""This logic right now works for testing locally, run the python script in terminal and 
its return the users since the date passed. user_login_tool.py is the same, just as MCP tool, needs to be tested and
used with claude, but by testing this file we know the logic works"""

def get_recent_logins(since_date: str):
    try:
        since = datetime.strptime(since_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        print("Invalid date format. Use YYYY-MM-DD.")
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

    url = f"{BASE_URL}/api/account?limit=500&offset=0&search=&with_teams=true"
    response = session.get(url)
    response.raise_for_status()
    data = response.json()

    users = []
    #print(data[0])
    for user in data:
        last_login_str = user.get("last_login")
        if last_login_str:
            last_login = datetime.fromisoformat(last_login_str.replace("Z", "+00:00"))
            if last_login >= since:
                users.append({
                    #"id": user.get("id"),
                    "name": user.get("username"),
                    "last_login": last_login_str
                })

    if not users:
        print(f"No users logged in since {since_date}.")
    else:
        print(f"Users logged in since {since_date}:")
        for u in users:
            #print(f"- {u['name']} (ID: {u['id']}) | Last login: {u['last_login']}")
            print(f"- {u['name']}  | Last login: {u['last_login']}")

if __name__ == "__main__":
    get_recent_logins("2025-09-01")
