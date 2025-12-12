# 🤖 OPSREADY MCP AGENT

Welcome to the OpsReady MCP Agent, a proof-of-concept AI assistant designed to help organizations effortlessly understand and interact with their operational data. This project blends modern AI, backend engineering, and the **Model Context Protocol (MCP)** to create a seamless, natural-language interface for querying and analyzing real-world operational datasets.

---

## 🧭 Table of Contents

- [Introduction](#-introduction)
- [Features](#-features)
- [Technologies Used](#-technologies-used)
- [Design & Architecture](#design--architecture)
- [Prerequisites](#-prerequisites)
- [Installation and Setup](#%EF%B8%8F-installation-and-setup)
- [Adding Tools](#adding-tools)
- [Usage](#-usage)
- [License](#-license)

---

## ✨ Introduction

This project aims to make it simple and intuitive for companies using OpsReady to query and understand the operational data they generate. It demonstrates how an AI-powered agent, integrated through the MCP, can retrieve, interpret, and analyze large datasets through natural language—removing the need for manual data inspection.

---

## 🚀 Features

- **Speech-to-Text Input**
  Hold the **LEFT SHIFT** key to record your voice. The recording is automatically transcribed and saved for the AI agent to read.

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

## 💻 Technologies Used

| Category | Component | Description |
| :--- | :--- | :--- |
| **Backend & Core** | Python 3.10+, fastmcp, requests, dotenv | Main backend language, MCP framework, API communication, credential management. |
| **AI Integration** | Model Context Protocol (MCP), Claude Desktop App | Connects your local tools to the AI interface. |
| **Voice Input** | Whisper.cpp, pynput, sounddevice, scipy, numpy | Local speech-to-text engine, key detection, audio capture, and file processing. |

---

## Design & Architecture

There are two main components to the MCP System we designed. There is a Server.py file that connects our backend tools to Claude, and then there is a Tools folder which contains all of our tools.

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

## ✅ Prerequisites

1.  **Internet Access**
2.  **Python 3.10 or higher**: [Download Link](https://www.python.org/downloads/)
3.  **Claude Desktop App**: [Download Link](https://claude.com/download)
4.  **OpsReady Credentials**: A valid username and password for the OpsReady sandbox environment.
5.  **System Tools** (Required for Whisper compilation): **CMake** and **FFmpeg**.

---



## ⚙️ Installation and Setup

### 1. Prepare the Environment & Install All Libraries

1.  **Download** the repository and navigate to the project folder.
2.  Run this single command to install all Python libraries needed for the core server and voice listener:
    ```bash
    pip install mcp python-dotenv requests typing sounddevice scipy numpy pynput
    ```

### 2. Voice Input Engine Setup (Whisper.cpp)

The voice feature requires system dependencies and compilation.

#### 2A. Install System Dependencies (CMake & FFmpeg)

| Operating System | Action | Command/Instructions |
| :--- | :--- | :--- |
| **macOS** | Use Homebrew to install packages: | `brew install cmake ffmpeg` |
| **Linux (Debian/Ubuntu)** | Use the `apt` package manager: | `sudo apt update && sudo apt install cmake ffmpeg` |
| **Windows** | **Manual Installation and PATH Configuration:** | **[See Detailed Windows Steps Below]** |

##### **Windows Detailed Installation Steps**

1.  **CMake:** Download and install the Windows x64 Installer from [cmake.org]. **CRUCIAL:** Select **"Add CMake to system PATH for all users"** during installation.
2.  **FFmpeg:** Download a recent Windows build (e.g., from Gyan). Unzip the folder to a stable location (e.g., `C:\ffmpeg`).
3.  **Configure PATH:** You must add the path to the FFmpeg `/bin` directory (e.g., `C:\ffmpeg\bin`) to your Windows **system environment variables** (under **Path** variable).

#### 2B. Compile Whisper

*Run these commands from the root of your project directory.*

1.  Download the Whisper source code:
    ```bash
    git submodule update --init --recursive
    ```
2.  Compile the executable:
    ```bash
    cd background/whisper.cpp
    mkdir build && cd build
    cmake ..
    make
    ```
3.  Download the language model:
    ```bash
    cd ../models
    curl -O [https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin](https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin)
    ```
4.  **Verify Paths:** The Python tools expect these files to be present: `background/whisper.cpp/build/bin/whisper-cli` and `background/whisper.cpp/models/ggml-base.en.bin`.

### 3. Authentication & Configuration

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

## ▶️ Usage

To utilize the tools, you must run two separate terminal sessions: one for the core server and one for the voice listener.

| Component | Command | Location |
| :--- | :--- | :--- |
| **1. Core MCP Server** | `python3 server.py` | Project Root Directory |
| **2. Voice Listener** | `python3 background/voice_output.py` | Project Root Directory |

### Command Input

| Method | Action | Example |
| :--- | :--- | :--- |
| **Voice Command** | Hold **LEFT SHIFT** to speak. Release to transcribe. Then, type `"Get voice input"` into the Claude chat box. | *Query:* "List all assets." *Claude Input:* `Get voice input` |
| **Text Input** | Directly type your query into the Claude chat box. | `Open workorders for Summit Base` |

> **Stop Servers:** Stop both running servers using **CTRL + C** in their respective terminal windows.

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


## 📜 License

### Data Usage and Retrieval

**The data accessed, retrieved, or displayed by this software is not governed by any implied license.**

All operational data, credentials, and configuration accessed through the OpsReady APIs remain the exclusive intellectual property of **OpsReady** and the client organization.

* **Data Rights:** Access to the data is governed solely by the terms of service and licensing agreement established between the user's organization and OpsReady.
* **Sandbox Environment:** This tool is designed to retrieve data from the OpsReady sandbox environment (`https://or-student-sandbox.opsready.com`). Use of this tool is subject to the conditions and restrictions governing that specific sandbox instance.
* **Security:** Users are responsible for maintaining the security and confidentiality of their OpsReady credentials stored in the local `.env` file.



















































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

## Adding New Tools
The way we designed our MCP server makes it very easy to add and remove tools from Claude.

### Adding to Servery.py

Usually the first step to adding a new tool is to add the tools description to Server.py. Although there is no required order to adding a new tool, adding the tool description first allows you to understand what the tool needs.

Use this template to add a new tool to Server.py. The tool description must be added in the function list_tools() function, as described in [Architecture & Design](#architecture).
```
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









  
