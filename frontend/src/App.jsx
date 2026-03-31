import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  
  
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  const API_BASE_URL = 'https://opsready-chatbot-d7i9.vercel.app';

  const tasks = [
    { title: "Inspect Fire Extinguishers - Building A", assigned: "Sarah Johnson", status: "In Progress", priority: "PRIORITY" },
    { title: "Replace HVAC Filters - Floor 3", assigned: "Mike Chen", status: "Open", priority: "ROUTINE" },
    { title: "Emergency Exit Sign Repair", assigned: "Unassigned", status: "Open", priority: "EMERGENCY" },
    { title: "Monthly Safety Inspection", assigned: "David Martinez", status: "Complete", priority: "ROUTINE" },
    { title: "Boiler Maintenance Check", assigned: "Sarah Johnson", status: "Open", priority: "PRIORITY" }
  ];
  
  const workOrders = [
    { number: "WO-2024-001", asset: "Plumbing System", status: "Open", desc: "Leaking pipe in basement" },
    { number: "WO-2024-002", asset: "Elevator - Main", status: "Closed", desc: "Maintenance completed" }
  ];
  
  const deficiencies = [
    { id: "DEF-001", name: "Cracked window in lobby", status: "Unresolved" },
    { id: "DEF-002", name: "Broken door handle - Room 205", status: "Unresolved" }
  ];

  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.onresult = (event) => {
        setInputValue(event.results[0][0].transcript);
        setIsRecording(false);
      };
    }
  }, []);

  const scrollToBottom = () => messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;
    const userMessage = inputValue.trim();
    setInputValue('');
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);
    
    try {
      const updatedHistory = [...conversationHistory, { role: 'user', content: userMessage }];
      const response = await fetch(`${API_BASE_URL}/api/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          message: userMessage, 
          conversation_history: updatedHistory
        })
      });
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      setConversationHistory(data.conversation_history);
    } catch (error) {
      console.error("Fetch Error:", error);
      setMessages(prev => [...prev, { role: 'assistant', content: "API Error: Please check the browser console for details." }]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="dashboard-wrapper">
      <nav className="side-nav">
        <div className="logo">OpsReady</div>
        <ul>
          <li className="active">Dashboard</li>
          <li>Assets</li>
          <li>Work Orders</li>
          <li>Team</li>
        </ul>
      </nav>

      <main className="main-content">
      <header className="top-bar">
        <h2>Facility Overview: Building A</h2>
        <div className="user-profile">👤 Gesi Morris-Odubo</div>
      </header>

      <section className="stats-grid">
        <div className="stat-card"><h3>{tasks.length}</h3><p>Active Tasks</p></div>
        <div className="stat-card"><h3>{workOrders.length}</h3><p>Open Orders</p></div>
        <div className="stat-card warning"><h3>{deficiencies.length}</h3><p>Deficiencies</p></div>
      </section>

      <section className="data-table">
        <h3>Maintenance Schedule</h3>
        <table>
          <thead>
            <tr><th>Task</th><th>Assigned To</th><th>Status</th><th>Priority</th></tr>
          </thead>
          <tbody>
            {tasks.map((t, i) => (
              <tr key={i}>
                <td>{t.title}</td>
                <td>{t.assigned}</td>
                <td><span className={`badge ${t.status.toLowerCase().replace(' ', '-')}`}>{t.status}</span></td>
                <td style={{ color: t.priority === 'EMERGENCY' ? '#991b1b' : 'inherit', fontWeight: t.priority === 'EMERGENCY' ? 'bold' : 'normal' }}>
                {t.priority}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="data-table" style={{ marginTop: '20px' }}>
        <h3>System Work Orders</h3>
        <table>
          <thead>
            <tr><th>ID</th><th>Asset</th><th>Description</th><th>Status</th></tr>
          </thead>
          <tbody>
            {workOrders.map((wo, i) => (
              <tr key={i}>
                <td>{wo.number}</td>
                <td>{wo.asset}</td>
                <td>{wo.desc}</td>
                <td><span className={`badge ${wo.status.toLowerCase()}`}>{wo.status}</span></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </main>

      <button className="chat-trigger" onClick={() => setIsChatOpen(!isChatOpen)}>
        {isChatOpen ? '✕' : '!'}
      </button>

      {isChatOpen && (
        <div className="chat-widget">
          <div className="chat-header">
            <h4>OpsReady AI Assistant</h4>
            <span>Online</span>
          </div>
          <div className="messages-area">
            {messages.length === 0 ? (
              <div className="welcome">How can I help with facility operations today?</div>
            ) : (
              messages.map((msg, i) => (
                <div key={i} className={`msg-bubble ${msg.role}`}>{msg.content}</div>
              ))
            )}
            <div ref={messagesEndRef} />
          </div>
          <div className="chat-input-row">
            <input 
              value={inputValue} 
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && sendMessage()}
              placeholder="Ask OpsReady..."
            />
            <button onClick={sendMessage}>➤</button>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;