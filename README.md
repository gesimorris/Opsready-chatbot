## This project is split into two phases. Phase 1 was worked on as a capstone project with two other team members. Phase 2 was worked on independetly by me. ##

# Phase 1

# OPSREADY MCP AGENT

Welcome to the OpsReady MCP Agent, a proof-of-concept AI assistant designed to help organizations effortlessly understand and interact with their operational data. This project blends modern AI, backend engineering, and the Model Context Protocol (MCP) to create a seamless, natural-language interface for querying and analyzing real-world operational datasets.

---

## 🧭 Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Technologies Used](#technologies-used)
- [Design & Architecture](#design--architecture)
- [Prerequisites](#prerequisites)
- [Installation and Setup](#installation-and-setup)
- [Adding Tools](#adding-tools)
- [Usage](#usage)
- [License](#license)

---

## Introduction

This project aims to make it simple and intuitive for companies using OpsReady to query and understand the operational data they generate. It demonstrates how an AI-powered agent, integrated through the MCP, can retrieve, interpret, and analyze large datasets through natural language—removing the need for manual data inspection.

---

## Features

- **OpsReady Tools Integration**
  The AI agent can interact with various OpsReady endpoints to retrieve operational data:
  | Tool Function | Description |
  | :--- | :--- |
  | **Get Activity Feed** | Fetch recent activity within the workspace. |
  | **Get User Logins** | List users who have logged in since a specific date. |
  | **Get Tasks** | Retrieve tasks assigned to users (overdue, upcoming, all). |
  | **List Forms** | Fetch available forms and their IDs in the workspace. |
  | **Get Assets** | Retrieve assets associated with a workspace. |
  | **Team-Specific Tasks** | List tasks assigned to specific teams. |
  | **Deficiencies** | Retrieve reported deficiencies for a workspace. |
  | **Work Orders** | Retrieve open or closed work orders. |

---

## Technologies Used

| Category | Component | Description |
| :--- | :--- | :--- |
| **Backend & Core** | Python 3.10+, fastmcp, requests, dotenv | Main backend language, MCP framework, API communication, credential management. |
| **AI Integration** | Model Context Protocol (MCP), Claude Desktop App | Connects your local tools to the AI interface. |

---

## Design & Architecture

There are two main components to the MCP System we designed. There is a server.py file that connects our backend tools to Claude, and then there is a Tools folder which contains all of our tools.

### Server.py
Server.py is exposed to Claude through a path saved in Claudes config file (more on this in Installation Section). The servers role is to define all of our tools in JSON Schema formatting. There is a python fucntion called list_tools() that contains all of the tools that Claude can access. @app.list_tool() as seen in the first line of the code sample below, is MCP's way of telling the model, in our case Claude, what the available tools are.

Example tool declaration that requires a since date, then returns the list of users signed in since that date.
```python
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
    ]

```
Server.py also contains a python function to call the tools called call_tools(). The function tells Claude to call this function when it wants to execute a tool by including @app.call_tool(), then Claude passes the tool name it wants to execute and any paramaters like workspace name to the function. 

Inside the call_tool() function there are elif statements that execute the correct too based on the tool name that Claude wants to execute.

Example of the call_tools() function:
```python
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

```python
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
```python
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
```python
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

---

## Prerequisites

1.  **Internet Access**
2.  **Python 3.10 or higher**: [Download Link](https://www.python.org/downloads/)
3.  **Claude Desktop App**: [Download Link](https://claude.com/download)
4.  **OpsReady Credentials**: A valid username and password for the OpsReady sandbox environment.
5.  **System Tools** (Required for Whisper compilation): **CMake** and **FFmpeg**.

---


## Installation and Setup

### 1. Prepare the Environment & Install All Libraries

1.  **Download** the repository and navigate to the project folder.
2.  Run this single command to install all Python libraries needed for the core server and voice listener:
    ```bash
    pip install mcp python-dotenv requests typing pynput
    ```

### 2. Authentication & Configuration

1.  **Authentication:** In the project root, create a file named **`.env`** and add your credentials:
    ```env
    OPSREADY_USERNAME=your_email@example.com
    OPSREADY_PASSWORD=your_password
    ```

2.  **MCP Config File:** Determine the **exact, absolute path** to your project folder. Create a file named **`mcp_config.json`** and paste this, **updating the `cwd` path**:
    ```json
    {
      "command": "python3",
      "args": [
        "server.py"
      ],
      "cwd": "PATH/TO/YOUR/PROJECT/FOLDER"
    }
    ```
    **CRUCIAL** Make sure to update the `cwd` key with the absolute path to your folder.

3.  **Load Config in Claude:**
    * Open Claude Desktop $\rightarrow$ **Settings** $\rightarrow$ **Developer**.
    * Find **"Load MCP Servers"** and click the button to select the **`mcp_config.json`** file.
    * **Restart Claude Desktop** and check the Developer tab to verify the server is "running."

---

## Usage

To utilize the tools, you must run two separate terminal sessions: one for the core server and one for the voice listener.

| Component | Command | Location |
| :--- | :--- | :--- |
| **Core MCP Server** | `python3 server.py` | Project Root Directory |

### Command Input

| Method | Action | Example |
| :--- | :--- | :--- |
| **Text Input** | Directly type your query into the Claude chat box. | `Open workorders for Summit Base` |

> **Stop Servers:** Stop running servers using **CTRL + C** in their respective terminal windows.

---

## Adding Tools
The way we designed our MCP server makes it very easy to add and remove tools from Claude.

### Adding to Servery.py

Usually the first step to adding a new tool is to add the tools description to Server.py. Although there is no required order to adding a new tool, adding the tool description first allows you to understand what the tool needs.

Use this template to add a new tool to Server.py. The tool description must be added in the function list_tools() function, as described in [Design & Architecture](#design--architecture).
```python
        Tool(
            name="tool_name_here",
            description="Tool description here (what the tool does)",
            inputSchema={
                "type": "object",
                "properties": {   #Paramaters your tool will take
                    "param_name (any name) ": {
                        "type": "string",    #type of paramater (Int, String, etc)
                        "description": "Description of the paramater here",
                    }
                },
                "required": ["since_date"]     #any paramaters that are required must be set as required
            }
        ),
```

Additionally, in Server.py you need to add the actual tool call

Use this template to add a tool call. The call must be added in the function call_tool(), as described in [Design & Architecture](#design--architecture).
```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Handle tool calls."""
    if name == "get_recent_logins":
        return await get_recent_logins(arguments["since_date"])
```

### Adding to Tools Folder
As of now, all of our tools are kept in the folder "tools", this is just for code cleanliness and does not need to be kept this way.
To add a tool there a few things that must be done:

Create a new python file for your tool (ex: tool_get_users.py)

Import the required packages and methods
```python
import os
from typing import List
from dotenv import load_dotenv
from mcp.types import TextContent
from opsready import get_tgt, get_st, get_api_session   #this allows us to use the methods we created to authenticate
```
Directly below load the username and password from .env
```python
load_dotenv()
BASE_URL = "https://or-student-sandbox.opsready.com"
USERNAME = os.getenv("OPSREADY_USERNAME")
PASSWORD = os.getenv("OPSREADY_PASSWORD")
```
Then you can create your tool method, ** Use async methods so Claude is not blocked ** 

Authentication is also needed in each tool, make this your first step of any new tool
```python
async def get_deficiency_details(deficiency_id: str) -> List[TextContent]:   #takes in deficiency id as string, returns List of TextContent (needed for MCP output)
    

    try:
        tgt = get_tgt(USERNAME, PASSWORD)   #call get_tgt() from opsready file
        if not tgt:
            print("failed to get TGT")
            return [TextContent(type="text", text="Failed to get TGT")]

        service_url = f"{BASE_URL}/api/login"
        st = get_st(tgt, service_url)     #call get_st() and pass it tgt and the service url (login url)
        session = get_api_session(st)    #get the authenticated session

        response = session.get(all_ws_url)
        response.raise_for_status()
        data = response.json()
```
We can see that the method takes in a string which is the deciciency_id, the method is required to take in the paramaters you declared it to accept in Server.py

From here, you can create the tool to call different APIs and use the data as you need to return the appropriate output


## License

### Data Usage and Retrieval

**The data accessed, retrieved, or displayed by this software is not governed by any implied license.**

All operational data, credentials, and configuration accessed through the OpsReady APIs remain the exclusive intellectual property of **OpsReady** and the client organization.

* **Data Rights:** Access to the data is governed solely by the terms of service and licensing agreement established between the user's organization and OpsReady.
* **Sandbox Environment:** This tool is designed to retrieve data from the OpsReady sandbox environment (`https://or-student-sandbox.opsready.com`). Use of this tool is subject to the conditions and restrictions governing that specific sandbox instance.
* **Security:** Users are responsible for maintaining the security and confidentiality of their OpsReady credentials stored in the local `.env` file.

# Phase 2

The goal of this phase was to create a frontend for users to use instead of directly interacting with Claude. There was the limiation that I lost access to the student-sandbox account so cannot access the data. So for this I decided to build two versions. Version A that works with a username and password for sandbox but can't be tested. Version B that works using mock data provided by myself that can be tested. Version A is the api_server.py file and Version B is main.py.


## 🏗️ Architecture

```
React Frontend
    ↓ HTTP
FastAPI Backend
    ↓ Anthropic API
Claude Sonnet 4
    ↓ Tool Calls
OpsReady API (Python tools)
```
Browsers enforce a Same-Origin Policy. Since the frontend is hosted on vercel.app and the backend is on a different domain, the browser naturally blocks the frontend from reaching out to a different server to fetch data. 

The CORSMiddleware acts as an "Access Control List." It tells the browser: "I trust requests coming from these specific Vercel and Localhost URLs, so please allow them to read my responses."

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React dev
        "http://localhost:5173",  # Vite dev
        "https://*.vercel.app",   # Vercel deployment
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```
I implemented these Pydantic models to define a strict schema for the chat interface. By using ChatMessage and ChatResponse, the API can automatically validate that incoming user messages and the conversation_history are formatted correctly before any processing happens. Since LLMs are 'stateless', I chose a List[Dict] structure to store the rolling history of the conversation. This allows the frontend to pass the entire context back to the server with every new message, ensuring the AI maintains a coherent and continuous dialogue."

```python
class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = []

class ChatResponse(BaseModel):
    response: str
    conversation_history: List[Dict[str, Any]]
```
The tool setup needed to be changed to fit the Claude API instead of MCP

```python
TOOLS = [
    {
        "name": "get_recent_logins",
        "description": "Returns users who have logged in since a certain date (YYYY-MM-DD)",
        "input_schema": {
            "type": "object",
            "properties": {
                "since_date": {
                    "type": "string",
                    "description": "Date in YYYY-MM-DD format"
                }
            },
            "required": ["since_date"]
        }
    },
```

### POST /api/chat
Main chat endpoint. Sends message to Claude, executes tools, returns response.

**Request:**
```json
{
  "message": "Show me overdue tasks",
  "conversation_history": []
}
```

**Response:**
```json
{
  "response": "Here are the overdue tasks...",
  "conversation_history": [...]
}
```

### GET /api/health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-02-14T...",
  "tools_available": 14
}
```

## 🚀 Setup Instructions

### Prerequisites

- Python 3.9+
- Node.js 18+
- Anthropic API key
- OpsReady sandbox credentials

### Step 1: Environment Variables

Create `.env` file in the root directory:

```bash
# Anthropic API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# OpsReady Credentials
OPSREADY_USERNAME=your_opsready_username
OPSREADY_PASSWORD=your_opsready_password
BASE_URL=https://or-student-sandbox.opsready.com
```

### Step 2: Backend Setup

```bash
# Install Python dependencies
cd backend
pip install -r requirements.txt

# Run the FastAPI server
python api_server.py
or
# Run mock demo
python main.py

# Server will start on http://localhost:8000
# Check health: http://localhost:8000/api/health
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will open at http://localhost:3000
```

## 🧪 Testing the Chat

Once both servers are running:

1. Open http://localhost:3000 in your browser
2. Try these example queries:
   - "Show me all overdue tasks"
   - "What work orders are open?"
   - "Who has logged in since 2025-01-01?"
   - "Get me a summary report of all tasks"
   - "Show me deficiencies in Summit Base"

## 🔧 Available Tools

The chatbot has access to 14+ tools:

### Tasks
- `get_user_tasks` - Get tasks by user
- `get_task_sample` - Sample tasks for debugging
- `get_all_assigned_users` - Users with task counts
- `get_overdue_tasks` - All overdue tasks
- `get_task_summary_report` - Task analytics
- `get_task_assignee` - Tasks by workspace
- `get_team_tasks` - Tasks by team

### Work Orders
- `get_work_orders` - Work orders with optional status filter

### Deficiencies
- `get_workspace_deficiencies` - Deficiencies by workspace
- `get_deficiency_details` - Detailed deficiency info

### Assets
- `get_assets` - Assets by workspace

### Other
- `get_recent_logins` - User login history
- `get_activity_feed` - Workspace activity
- `get_workspace_forms` - Forms list






























































  
