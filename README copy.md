# OpsReady AI Chatbot

An AI-powered chatbot for querying and managing OpsReady workplace operations data. Built with FastAPI (Python backend) + React (frontend) + Claude API.

## 🎯 Features

- **Real-time Data Access**: Query tasks, work orders, deficiencies, assets, and more
- **Natural Language Interface**: Ask questions in plain English
- **Voice Input**: Use speech-to-text for hands-free queries
- **14+ Tools**: Comprehensive access to OpsReady data
- **Agentic AI**: Claude automatically calls the right tools to answer your questions

## 🏗️ Architecture

```
React Frontend (Port 3000)
    ↓ HTTP
FastAPI Backend (Port 8000)
    ↓ Anthropic API
Claude Sonnet 4
    ↓ Tool Calls
OpsReady API (Python tools)
```

## 📁 Project Structure

```
opsready-chatbot/
├── api_server.py          # FastAPI backend with Claude integration
├── opsready.py            # OpsReady authentication
├── server.py              # Old MCP server (for reference)
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables (create this)
├── tools/                 # All OpsReady API tool functions
│   ├── tool_recent_logins.py
│   ├── tool_get_user_tasks.py
│   ├── tool_get_overdue_tasks.py
│   ├── tool_work_orders.py
│   └── ... (14+ tools)
└── opsready-frontend/     # React chat interface
    ├── package.json
    ├── vite.config.js
    ├── index.html
    └── src/
        ├── App.jsx        # Main chat component
        ├── App.css        # Styles
        ├── main.jsx       # Entry point
        └── index.css
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
pip install -r requirements.txt

# Run the FastAPI server
python api_server.py

# Server will start on http://localhost:8000
# Check health: http://localhost:8000/api/health
```

### Step 3: Frontend Setup

```bash
# Navigate to frontend directory
cd opsready-frontend

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

## 🚢 Deployment

### Backend Deployment (Railway/Render)

**Railway:**
```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up

# Add environment variables in Railway dashboard
```

**Render:**
1. Push code to GitHub
2. Create new Web Service on Render
3. Connect repository
4. Build command: `pip install -r requirements.txt`
5. Start command: `uvicorn api_server:app --host 0.0.0.0 --port $PORT`
6. Add environment variables in Render dashboard

### Frontend Deployment (Vercel)

```bash
# Install Vercel CLI
npm install -g vercel

# Navigate to frontend directory
cd opsready-frontend

# Deploy
vercel

# Update API URL in App.jsx to your deployed backend URL
```

**Or use Vercel Dashboard:**
1. Push code to GitHub
2. Import project in Vercel
3. Set root directory to `opsready-frontend`
4. Deploy

**Important:** Update the API URL in `App.jsx`:
```javascript
// Change from:
const response = await fetch('http://localhost:8000/api/chat', ...

// To:
const response = await fetch('https://your-backend-url.railway.app/api/chat', ...
```

## 🎤 Voice Input

Voice input uses the Web Speech API (Chrome, Edge, Safari only):
- Click the microphone button 🎤
- Speak your question
- Click again to stop recording (or it auto-stops)
- Your speech is converted to text

## 🐛 Troubleshooting

### Backend Issues

**"Failed to get TGT"**
- Check `.env` file has correct OpsReady credentials
- Verify BASE_URL is correct

**"ANTHROPIC_API_KEY not found"**
- Add your API key to `.env` file
- Get one at: https://console.anthropic.com/

**CORS errors:**
- Make sure backend `CORSMiddleware` allows your frontend origin
- Update `allow_origins` in `api_server.py` if deploying to custom domain

### Frontend Issues

**"Failed to fetch" / Network error:**
- Ensure backend is running on port 8000
- Check console for exact error message
- Verify firewall isn't blocking port 8000

**Voice input not working:**
- Only works in Chrome, Edge, Safari (not Firefox)
- Requires HTTPS in production (HTTP okay for localhost)
- Check browser permissions for microphone access

## 📊 API Endpoints

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

## 🔐 Security Notes

- **Never commit `.env` file** - Add to `.gitignore`
- **OpsReady credentials** are stored in `.env` only
- **API keys** should be kept secret
- **CORS** is configured for localhost dev - update for production

## 📝 Development Notes

### Adding New Tools

1. Create tool function in `tools/tool_name.py`
2. Import in `api_server.py`
3. Add tool definition to `TOOLS` array
4. Add case in `call_tool_function()`

### Modifying System Prompt

Edit `SYSTEM_PROMPT` in `api_server.py` to change Claude's behavior.

### Styling Changes

Edit `opsready-frontend/src/App.css` for UI changes.

## 📄 License

Private project for portfolio demonstration.

## 🎓 Built For

Full-stack developer portfolio demonstrating:
- Python backend development
- React frontend development
- AI/LLM integration
- RESTful API design
- Real-world tool integration

---

**Live Demo:** [Add your deployed URL here]
**GitHub:** [Add your repo URL here]
