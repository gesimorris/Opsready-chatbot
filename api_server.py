"""
OpsReady Chatbot API Server
Converts MCP tools to REST API endpoints and integrates with Claude API
"""
import os
import sys
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

# Add tools directory to path
sys.path.append(os.path.dirname(__file__))

# Import all tool functions
from tools.tool_recent_logins import get_recent_logins
from tools.tool_get_user_tasks import get_user_tasks
from tools.tool_debug_tasks_sample import get_task_sample
from tools.tool_get_all_assigned_users import get_all_assigned_users
from tools.tool_get_overdue_tasks import get_overdue_tasks
from tools.tool_get_task_summary_report import get_task_summary_report
from tools.tool_task_asignee import get_task_assignee
from tools.tool_activity_feed import get_activity_feed
from tools.tool_list_forms import get_workspace_forms_tool
from tools.tool_get_asset_deficiencies import get_asset_deficiencies
from tools.tool_work_orders import get_work_orders
from tools.get_deficiency_details import get_deficiency_details
from tools.tool_get_assets import get_assets
from tools.tool_teams_tasks import get_team_tasks

load_dotenv()

# Initialize FastAPI
app = FastAPI(title="OpsReady Chatbot API")

# CORS Configuration - allow React frontend
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

# Initialize Anthropic client
client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = []

class ChatResponse(BaseModel):
    response: str
    conversation_history: List[Dict[str, Any]]

# Tool definitions for Claude API (converted from MCP format)
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
    {
        "name": "get_user_tasks",
        "description": "Get all tasks assigned to a specific user by name, username, or email",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {
                    "type": "string",
                    "description": "Name, username, or email of the user"
                }
            },
            "required": ["identifier"]
        }
    },
    {
        "name": "get_task_sample",
        "description": "Return a small sample of tasks with basic fields for debugging",
        "input_schema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "How many tasks to show (default 5)",
                    "default": 5
                }
            }
        }
    },
    {
        "name": "get_all_assigned_users",
        "description": "List all users who currently have one or more tasks assigned, with task counts",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_overdue_tasks",
        "description": "List all tasks whose due date is before today (UTC)",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_task_summary_report",
        "description": "Generate a summary report of all OpsReady tasks: total, assigned/unassigned, overdue, due soon, and category breakdown",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_task_assignee",
        "description": "Retrieves task information from a given workspace. If the user asks for unassigned tasks, returns only those with no assignee",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_name": {
                    "type": "string",
                    "description": "The name of the workspace to get tasks from"
                },
                "unassigned_only": {
                    "type": "boolean",
                    "description": "If true, returns only tasks without an assigned user",
                    "default": False
                }
            },
            "required": ["workspace_name"]
        }
    },
    {
        "name": "get_team_tasks",
        "description": "Get the tasks that are assigned to a team",
        "input_schema": {
            "type": "object",
            "properties": {
                "team_name": {
                    "type": "string",
                    "description": "The name of the team to get tasks from"
                }
            },
            "required": ["team_name"]
        }
    },
    {
        "name": "get_activity_feed",
        "description": "Returns the most active users in a workspace, who has submitted forms, and recent activity",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_name": {
                    "type": "string",
                    "description": "Name of the workspace"
                }
            },
            "required": ["workspace_name"]
        }
    },
    {
        "name": "get_workspace_forms",
        "description": "Returns all available forms (and their IDs) for a specific OpsReady workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_name": {
                    "type": "string",
                    "description": "The name of the OpsReady workspace (e.g., 'Summit Base')"
                }
            },
            "required": ["workspace_name"]
        }
    },
    {
        "name": "get_workspace_deficiencies",
        "description": "Fetches all deficiencies for a given workspace and lists their status",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_name": {
                    "type": "string",
                    "description": "The name of the workspace to fetch deficiencies for"
                }
            },
            "required": ["workspace_name"]
        }
    },
    {
        "name": "get_deficiency_details",
        "description": "Fetches all details about a given deficiency, including task and work order info",
        "input_schema": {
            "type": "object",
            "properties": {
                "deficiency_id": {
                    "type": "string",
                    "description": "The deficiency ID"
                }
            },
            "required": ["deficiency_id"]
        }
    },
    {
        "name": "get_work_orders",
        "description": "Get work orders with optional status filter",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Status of work orders to filter by (e.g., 'Open', 'Closed')"
                }
            }
        }
    },
    {
        "name": "get_assets",
        "description": "Fetches all assets from a workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_name": {
                    "type": "string",
                    "description": "The workspace name"
                }
            },
            "required": ["workspace_name"]
        }
    }
]

# System prompt for Claude
SYSTEM_PROMPT = """You are an AI assistant for OpsReady, a workplace operations management platform. You help users query and manage:

- Tasks (assignments, due dates, priorities)
- Work orders (status, details, costs)
- Deficiencies (asset issues and status)
- Assets (equipment and inventory)
- Workspaces (organizational units)
- Teams (user groups)
- Activity feeds (recent actions)
- Forms (data collection tools)

You have access to tools that fetch real-time data from the OpsReady system. When users ask questions, use the appropriate tools to get accurate, current information.

Be helpful, concise, and professional. Format data clearly using markdown when appropriate."""

async def call_tool_function(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Execute the appropriate tool function based on tool name"""
    try:
        if tool_name == "get_recent_logins":
            result = await get_recent_logins(tool_input["since_date"])
        elif tool_name == "get_user_tasks":
            result = await get_user_tasks(tool_input["identifier"])
        elif tool_name == "get_task_sample":
            result = await get_task_sample(tool_input.get("limit", 5))
        elif tool_name == "get_all_assigned_users":
            result = await get_all_assigned_users()
        elif tool_name == "get_overdue_tasks":
            result = await get_overdue_tasks()
        elif tool_name == "get_task_summary_report":
            result = await get_task_summary_report()
        elif tool_name == "get_task_assignee":
            result = await get_task_assignee(
                tool_input["workspace_name"],
                tool_input.get("unassigned_only", False)
            )
        elif tool_name == "get_team_tasks":
            result = await get_team_tasks(tool_input["team_name"])
        elif tool_name == "get_activity_feed":
            result = await get_activity_feed(tool_input["workspace_name"])
        elif tool_name == "get_workspace_forms":
            result = await get_workspace_forms_tool(tool_input["workspace_name"])
        elif tool_name == "get_workspace_deficiencies":
            result = await get_asset_deficiencies(tool_input["workspace_name"])
        elif tool_name == "get_deficiency_details":
            result = await get_deficiency_details(tool_input["deficiency_id"])
        elif tool_name == "get_work_orders":
            result = await get_work_orders(status=tool_input.get("status"))
        elif tool_name == "get_assets":
            result = await get_assets(tool_input["workspace_name"])
        else:
            return f"Unknown tool: {tool_name}"
        
        # Extract text from TextContent objects
        if isinstance(result, list):
            return "\n".join([item.text for item in result if hasattr(item, 'text')])
        return str(result)
    
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Main chat endpoint - processes user message with Claude and tool execution"""
    try:
        # Build conversation history
        messages = request.conversation_history + [
            {"role": "user", "content": request.message}
        ]
        
        # Initial Claude API call
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )
        
        # Handle tool use (agentic loop)
        while response.stop_reason == "tool_use":
            # Extract tool calls
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            
            # Execute each tool
            tool_results = []
            for tool_use in tool_use_blocks:
                tool_result = await call_tool_function(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result
                })
            
            # Add assistant response and tool results to conversation
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            # Continue conversation with tool results
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            )
        
        # Extract final text response
        final_response = ""
        for block in response.content:
            if hasattr(block, 'text'):
                final_response += block.text
        
        # Update conversation history
        messages.append({"role": "assistant", "content": final_response})
        
        return ChatResponse(
            response=final_response,
            conversation_history=messages
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "tools_available": len(TOOLS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
