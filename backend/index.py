"""
OpsReady Chatbot API Server - Mock Demo Mode
Fully synchronized with frontend data structures and updated for Claude Haiku 4.5.
"""
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import anthropic

load_dotenv()

app = FastAPI(title="OpsReady Chatbot API (Demo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_origin_regex=r"https://opsready-chatbot.*\.vercel\.app", 
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)

client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

MODEL_ID = "claude-haiku-4-5-20251001"

class ChatMessage(BaseModel):
    message: str
    conversation_history: Optional[List[Dict[str, Any]]] = []

class ChatResponse(BaseModel):
    response: str
    conversation_history: List[Dict[str, Any]]

# =====================================================================
#                          MCP TOOL SCHEMAS
# =====================================================================
TOOLS = [
    {
        "name": "get_maintenance_schedule",
        "description": "Returns all active facility maintenance tasks, priorities, statuses, and assignees.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_system_work_orders",
        "description": "Fetches high-level tracking data for active system work orders.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_facility_deficiencies",
        "description": "Lists structural, aesthetic, or immediate physical facility deficiencies.",
        "input_schema": {
            "type": "object",
            "properties": {}
        }
    }
]

SYSTEM_PROMPT = """You are an AI assistant for OpsReady, a workplace operations management platform. 
You assist facility operators with tracking maintenance schedules, work orders, and open structural deficiencies.

Your dashboard context contains real-time operational logs. When users ask questions about active operations, use your tools to provide data that matches exactly what they see on screen.

Be helpful, concise, and professional. 

CRITICAL FORMATTING RULE: Whenever you return lists of tasks, work orders, or deficiencies, you MUST format the data as a clean Markdown table with clear column headers (e.g., ID, Asset, Status). If a table cannot be used, format the data using clean, bolded bullet points. Do not wrap data inside dense paragraphs."""

# =====================================================================
#             SYNCHRONIZED INLINE MOCK OPERATIONAL DATA
# =====================================================================

async def call_tool_function(tool_name: str, tool_input: Dict[str, Any]) -> str:
    """Provides exact mock structural alignment with React state arrays"""
    try:
        if tool_name == "get_maintenance_schedule":
            return (
                "Active Maintenance Tasks:\n"
                "- **Inspect Fire Extinguishers - Building A** | Assigned to: Sarah Johnson | Status: In Progress | Priority: PRIORITY\n"
                "- **Replace HVAC Filters - Floor 3** | Assigned to: Mike Chen | Status: Open | Priority: ROUTINE\n"
                "- **Emergency Exit Sign Repair** | Assigned to: Unassigned | Status: Open | Priority: EMERGENCY\n"
                "- **Monthly Safety Inspection** | Assigned to: David Martinez | Status: Complete | Priority: ROUTINE\n"
                "- **Boiler Maintenance Check** | Assigned to: Sarah Johnson | Status: Open | Priority: PRIORITY"
            )
            
        elif tool_name == "get_system_work_orders":
            return (
                "System Work Orders:\n"
                "- **WO-2024-001**: Plumbing System - Leaking pipe in basement | Status: Open\n"
                "- **WO-2024-002**: Elevator - Main - Maintenance completed | Status: Closed"
            )
            
        elif tool_name == "get_facility_deficiencies":
            return (
                "Unresolved Facility Deficiencies:\n"
                "- **DEF-001**: Cracked window in lobby | Status: Unresolved\n"
                "- **DEF-002**: Broken door handle - Room 205 | Status: Unresolved"
            )
            
        else:
            return f"Unknown core service: {tool_name}"
            
    except Exception as e:
        return f"Error executing data pipe mock: {str(e)}"

# =====================================================================
#                        CHAT ROUTING PIPELINE
# =====================================================================

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatMessage):
    """Processes chat cycles using updated model configurations and inline data tools"""
    try:
        messages = request.conversation_history + [
            {"role": "user", "content": request.message}
        ]
        
        response = client.messages.create(
            model=MODEL_ID,
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOLS,
            messages=messages
        )
        
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
                model=MODEL_ID,
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
        raise HTTPException(status_code=500, detail=f"Internal Agent Loop Error: {str(e)}")

@app.get("/api/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "synchronized_records": True,
        "engine": MODEL_ID
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)