"""
Mock OpsReady API Server for Portfolio Demo
No real credentials needed - returns realistic fake data
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="OpsReady Chatbot API (Mock)")

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:5173",
        "https://*.vercel.app",
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

# MOCK DATA - Realistic fake data for demo
MOCK_TASKS = [
    {
        "title": "Inspect Fire Extinguishers - Building A",
        "assigned_to": {"name": "Sarah Johnson"},
        "status": "In Progress",
        "due_date": (datetime.now() - timedelta(days=2)).isoformat(),
        "priority": "PRIORITY"
    },
    {
        "title": "Replace HVAC Filters - Floor 3",
        "assigned_to": {"name": "Mike Chen"},
        "status": "Open",
        "due_date": (datetime.now() + timedelta(days=5)).isoformat(),
        "priority": "ROUTINE"
    },
    {
        "title": "Emergency Exit Sign Repair",
        "assigned_to": None,
        "status": "Open",
        "due_date": (datetime.now() - timedelta(days=1)).isoformat(),
        "priority": "EMERGENCY"
    },
    {
        "title": "Monthly Safety Inspection",
        "assigned_to": {"name": "David Martinez"},
        "status": "Complete",
        "due_date": (datetime.now() - timedelta(days=10)).isoformat(),
        "priority": "ROUTINE"
    },
    {
        "title": "Boiler Maintenance Check",
        "assigned_to": {"name": "Sarah Johnson"},
        "status": "Open",
        "due_date": (datetime.now() + timedelta(days=3)).isoformat(),
        "priority": "PRIORITY"
    }
]

MOCK_WORK_ORDERS = [
    {
        "number": "WO-2024-001",
        "workspace": "Summit Base",
        "status": "Open",
        "description": "Leaking pipe in basement",
        "asset": "Plumbing System - Building A",
        "created": "2024-01-15"
    },
    {
        "number": "WO-2024-002",
        "workspace": "North Station",
        "status": "Closed",
        "description": "Elevator maintenance completed",
        "asset": "Elevator - Main Building",
        "created": "2024-01-10"
    }
]

MOCK_DEFICIENCIES = [
    {"name": "Cracked window in lobby", "status": "Unresolved", "id": "DEF-001"},
    {"name": "Broken door handle - Room 205", "status": "Unresolved", "id": "DEF-002"},
    {"name": "Water stain on ceiling", "status": "Resolved", "id": "DEF-003"}
]

# Mock tool functions that return realistic data
async def mock_get_overdue_tasks() -> str:
    overdue = [t for t in MOCK_TASKS if datetime.fromisoformat(t["due_date"]) < datetime.now()]
    if not overdue:
        return "No overdue tasks found."
    
    lines = [f"Overdue tasks as of {datetime.now().strftime('%Y-%m-%d')}:"]
    for t in overdue:
        assigned = t["assigned_to"]["name"] if t["assigned_to"] else "Unassigned"
        lines.append(f"- {t['title']} | Assigned: {assigned} | Due: {t['due_date'][:10]}")
    lines.append(f"\nTotal overdue: {len(overdue)}")
    return "\n".join(lines)

async def mock_get_task_summary() -> str:
    total = len(MOCK_TASKS)
    assigned = sum(1 for t in MOCK_TASKS if t["assigned_to"])
    unassigned = total - assigned
    overdue = sum(1 for t in MOCK_TASKS if datetime.fromisoformat(t["due_date"]) < datetime.now())
    
    return f"""📊 OpsReady Task Summary Report

Total tasks: {total}
Assigned: {assigned}
Unassigned: {unassigned}
Overdue: {overdue}
Due soon (next 7 days): 2

Top task categories:
- Inspection: 2
- Maintenance: 2
- Repair: 1

Key insights:
• There are overdue tasks requiring attention.
• Several tasks are approaching their due dates.

✅ Summary complete."""

async def mock_get_work_orders(status: Optional[str] = None) -> str:
    orders = MOCK_WORK_ORDERS
    if status:
        orders = [w for w in orders if w["status"].lower() == status.lower()]
    
    if not orders:
        return "No work orders found."
    
    lines = []
    for wo in orders:
        lines.append(f"""Work Order: {wo['number']}
Workspace: {wo['workspace']}
Status: {wo['status']}
Description: {wo['description']}
Asset: {wo['asset']}
Date Created: {wo['created']}
---------------------------------------""")
    return "\n".join(lines)

async def mock_get_deficiencies(workspace: str) -> str:
    return f"""**Deficiencies in {workspace}:**
1. Cracked window in lobby — Unresolved - DEF-001
2. Broken door handle - Room 205 — Unresolved - DEF-002
3. Water stain on ceiling — Resolved - DEF-003"""

async def mock_get_user_tasks(identifier: str) -> str:
    user_tasks = [t for t in MOCK_TASKS if t["assigned_to"] and identifier.lower() in t["assigned_to"]["name"].lower()]
    if not user_tasks:
        return f"No tasks found for '{identifier}'."
    
    lines = [f"Tasks assigned to {identifier}:"]
    for t in user_tasks:
        lines.append(f"- {t['title']} | Status: {t['status']} | Due: {t['due_date'][:10]}")
    return "\n".join(lines)

async def mock_get_all_assigned_users() -> str:
    from collections import Counter
    users = [t["assigned_to"]["name"] for t in MOCK_TASKS if t["assigned_to"]]
    counts = Counter(users).most_common()
    
    lines = ["Users with assigned tasks:\n"]
    for name, count in counts:
        lines.append(f"- {name}: {count} task(s)")
    return "\n".join(lines)

async def mock_recent_logins(since_date: str) -> str:
    return f"""Users logged in since {since_date}:
- sarah.johnson@opsready.com (2024-01-20)
- mike.chen@opsready.com (2024-01-19)
- david.martinez@opsready.com (2024-01-18)"""

# Tool definitions for Claude
TOOLS = [
    {
        "name": "get_overdue_tasks",
        "description": "List all tasks whose due date is before today",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_task_summary_report",
        "description": "Generate a summary report of all tasks: total, assigned/unassigned, overdue, due soon",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_work_orders",
        "description": "Get work orders with optional status filter",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Status filter (e.g., 'Open', 'Closed')"}
            }
        }
    },
    {
        "name": "get_workspace_deficiencies",
        "description": "Get all deficiencies for a workspace",
        "input_schema": {
            "type": "object",
            "properties": {
                "workspace_name": {"type": "string", "description": "Workspace name"}
            },
            "required": ["workspace_name"]
        }
    },
    {
        "name": "get_user_tasks",
        "description": "Get all tasks assigned to a specific user",
        "input_schema": {
            "type": "object",
            "properties": {
                "identifier": {"type": "string", "description": "User name or email"}
            },
            "required": ["identifier"]
        }
    },
    {
        "name": "get_all_assigned_users",
        "description": "List all users with tasks and their task counts",
        "input_schema": {"type": "object", "properties": {}}
    },
    {
        "name": "get_recent_logins",
        "description": "Get users who logged in since a date (YYYY-MM-DD)",
        "input_schema": {
            "type": "object",
            "properties": {
                "since_date": {"type": "string", "description": "Date in YYYY-MM-DD format"}
            },
            "required": ["since_date"]
        }
    }
]

SYSTEM_PROMPT = """You are an AI assistant for OpsReady, a workplace operations management platform. You help users query and manage tasks, work orders, deficiencies, and assets.

IMPORTANT: This is a demo version with mock data for portfolio purposes. The data you're accessing is realistic but fake.

Be helpful, concise, and professional. Format data clearly using markdown when appropriate."""

async def call_tool_function(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Execute mock tool functions"""
    try:
        if tool_name == "get_overdue_tasks":
            return await mock_get_overdue_tasks()
        elif tool_name == "get_task_summary_report":
            return await mock_get_task_summary()
        elif tool_name == "get_work_orders":
            return await mock_get_work_orders(tool_input.get("status"))
        elif tool_name == "get_workspace_deficiencies":
            return await mock_get_deficiencies(tool_input["workspace_name"])
        elif tool_name == "get_user_tasks":
            return await mock_get_user_tasks(tool_input["identifier"])
        elif tool_name == "get_all_assigned_users":
            return await mock_get_all_assigned_users()
        elif tool_name == "get_recent_logins":
            return await mock_recent_logins(tool_input["since_date"])
        else:
            return f"Unknown tool: {tool_name}"
    except Exception as e:
        return f"Error executing {tool_name}: {str(e)}"

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Main chat endpoint"""
    try:
        messages = request.conversation_history + [
            {"role": "user", "content": request.message}
        ]
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )
        
        # Handle tool use (agentic loop)
        while response.stop_reason == "tool_use":
            tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
            
            tool_results = []
            for tool_use in tool_use_blocks:
                tool_result = await call_tool_function(tool_use.name, tool_use.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": tool_result
                })
            
            messages.append({"role": "assistant", "content": response.content})
            messages.append({"role": "user", "content": tool_results})
            
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=messages
            )
        
        final_response = ""
        for block in response.content:
            if hasattr(block, 'text'):
                final_response += block.text
        
        messages.append({"role": "assistant", "content": final_response})
        
        return ChatResponse(
            response=final_response,
            conversation_history=messages
        )
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")

@app.get("/api/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy (mock data)",
        "timestamp": datetime.now().isoformat(),
        "tools_available": len(TOOLS)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
