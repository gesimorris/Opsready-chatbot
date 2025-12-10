# Project Overview
This project is an MCP (Model Context Protocol) server that allows Claude to interact with internal company data
such as:
- Workspaces
- Deficiencies
- Tasks
- Assets
- Work Orders
- Activity
- Teams
- Accounts

It exposes a set of tools, which are API endpoints to Claude, so Claude can call and retrieve structured data and perform
queries. This enables a conversational style interface that allows users to get answers and insights into their operational data.

## Features:

### Authentication
- Authenticate each API call using user credentials
- Get TGT -> ST -> Session
- Ensure users are authroized to see data
- Respond with "Not Authorized" message in the case that a user is not authorized

### Workspace Tools
- Takes in workspace name
- Fetch all assets in a workspace
- Get the activity feed from any workspace
- Find tasks in workspaces

### Deficiency Tools
- Get details for deficiencies in workspaces
- Find if deficiencies have related tasks
- Get more information on deficiencies

### Task Tools
- Show tasks assigned to users
- Show unassigned or assigned tasks throughout the site
- Get tasks assigned to specific teams
- Get unnassigned vs assigned tasks

## Architecture & Design

There are two main components to the MCP System we designed. There is a Server.py file that connects our backend tools to Claude, and then there is a Tools folder which contains all of our tools.

### Server.py
Server.py is exposed to Claude through a path saved in Claudes config file (more on this in Installation Section). The servers role is to define all of our tools in JSON Schema formatting. There is a python fucntion called list_tools() that contains all of the tools that Claude can access. @app.list_tool() as seen in the first line of the code sample below, is MCP's way of telling the model, in our case Claude, what the available tools are.

Example tool declaration that requires a since date, then returns the list of users signed in since that date.
```
@app.list_tools()
async def list_tools() -> list[Tool]:
    return [
        Tool(
            name="get_recent_logins",
            description="Returns users who have logged in since certain date (YYYY-MM-DD)",
            inputSchema={
                "type": "object",
                "properties": {
                    "since_date": {
                        "type": "string",
                        "description": "Date in YYYY-MM-DD format",
                    }
                },
                "required": ["since_date"]
            }
        ),

```
Server.py also contains a python function to call the tools called call_tools(). The function tells Claude to call this function when it wants to execute a tool by including @app.call_tool(), then Claude passes the tool name it wants to execute and any paramaters like workspace name to the function. 

Inside the call_tool() function there are elif statements that execute the correct too based on the tool name that Claude wants to execute.

Example of the call_tools() function:
```
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""

    if name == "get_recent_logins":
        return await get_recent_logins(arguments["since_date"])
    elif name == "get_user_tasks":
        return await get_user_tasks(arguments["identifier"])
    elif name == "get_task_sample":
        return await get_task_sample(arguments.get("limit", 5))
    elif name == "get_all_assigned_users":
        return await get_all_assigned_users()
    elif name == "get_overdue_tasks":
        return await get_overdue_tasks()
    elif name == "get_task_summary_report":
        return await get_task_summary_report()
```
So whatever tool name Claude passes as a parameter to be executed, the call_tool() function executes it and then the output is returned back to the Server, then to Claude.

And finally the Server.py contains a main() function that implements MCP helper function stdio_server(), which creates the server as a read_stream and write_stream so Claude can see our server and is able to both read data and write date. The main() function also prints "Server Running" so the user can know its running.

```
async def main():
    from mcp.server.stdio import stdio_server  #import helper function from mcp package
    print("Server running")   
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())   #start the server as read and write
```

### Tools

Tools in MCP can be thought of as "Tasks" where each tool is a different task the agent can perform. Most tools call atleast one API to get the data from the backend site. Tools can call as many APIs as needed, and can even call other tools to get access to their data.

All of the tools that we created are contained in the "tools" folder, which is just a way to keep clean code structure so the files do not get messy. Tools can be kept anywhere.
Each tool needs to be declared in Server.py as in JSON Schema format under the @app.list_tools() section, this is how Claude is able to see the tool, also each tool must be called in the call_tools() function to be able to be executed.

Here is an example of how a tool is setup:
```
async def get_recent_logins(since_date: str) -> list[TextContent]:

    try:
        since = datetime.strptime(since_date, "%Y-%m-%d").replace(tzinfo=timezone.utc)
    except ValueError:
        return [TextContent(
            type="text",
            text="Invalid date format. Use YYYY-MM-DD."
        )]

    url = f"{BASE_URL}/api/account?limit=500&offset=0&search=&with_teams=true"

    try:
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            print("failed to get TGT")
            return [TextContent(type="text", text="Failed to get TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        session = get_api_session(st)
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return [TextContent(
            type="text",
            text=f"Failed to fetch accounts: {str(e)}"
        )]
```
This is the tool responsible for returning a list of users that have signed in from a passed date. It takes in the "since" date as a parameter and will return a TextContext List, which is the MCP object that is used to give data to Claude. 

Each tool is also required to authenticate when its called, to ensure the user is able to see the data:
```
try:
        tgt = get_tgt(USERNAME, PASSWORD)
        if not tgt:
            print("failed to get TGT")
            return [TextContent(type="text", text="Failed to get TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)
        session = get_api_session(st)
        response = session.get(url)
        response.raise_for_status()
        data = response.json()
```
This code calls functions that are created in our opsready.py, which is responsibe for getting tgt, st, and session instances for the user requesting data.

### Tool3:
- ipsum

### Tool4









  
