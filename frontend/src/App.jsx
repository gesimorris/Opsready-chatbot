import React, { useState, useRef, useEffect } from 'react';
import './App.css';

function App() {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [conversationHistory, setConversationHistory] = useState([]);
  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);

  // Initialize Speech Recognition
  useEffect(() => {
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
      const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
      recognitionRef.current = new SpeechRecognition();
      recognitionRef.current.continuous = false;
      recognitionRef.current.interimResults = false;
      recognitionRef.current.lang = 'en-US';

      recognitionRef.current.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setInputValue(transcript);
        setIsRecording(false);
      };

      recognitionRef.current.onerror = () => {
        setIsRecording(false);
      };

      recognitionRef.current.onend = () => {
        setIsRecording(false);
      };
    }
  }, []);

  // Auto-scroll to bottom
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleVoiceInput = () => {
    if (!recognitionRef.current) {
      alert('Speech recognition is not supported in your browser. Please use Chrome, Edge, or Safari.');
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      recognitionRef.current.start();
      setIsRecording(true);
    }
  };

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = inputValue.trim();
    setInputValue('');

    // Add user message to UI
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);

    try {
      const response = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage,
          conversation_history: conversationHistory
        })
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      // Add AI response to UI
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      
      // Update conversation history for context
      setConversationHistory(data.conversation_history);

    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { 
        role: 'assistant', 
        content: `Error: ${error.message}. Make sure the backend server is running on http://localhost:8000` 
      }]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const clearChat = () => {
    setMessages([]);
    setConversationHistory([]);
  };

  return (
    <div className="App">
      <div className="chat-container">
        {/* Header */}
        <div className="chat-header">
          <div className="header-content">
            <h1>OpsReady AI Assistant</h1>
            <p>Ask about tasks, work orders, assets, and more</p>
          </div>
          <button onClick={clearChat} className="clear-button">
            Clear Chat
          </button>
        </div>

        {/* Messages Area */}
        <div className="messages-container">
          {messages.length === 0 ? (
            <div className="welcome-message">
              <h2>👋 Welcome to OpsReady AI</h2>
              <p>I can help you with:</p>
              <ul>
                <li>📋 Viewing and managing tasks</li>
                <li>🔧 Checking work orders</li>
                <li>⚠️ Tracking deficiencies</li>
                <li>📦 Managing assets</li>
                <li>📊 Generating reports</li>
                <li>👥 Team and workspace info</li>
              </ul>
              <p>Try asking: "Show me overdue tasks" or "What work orders are open?"</p>
            </div>
          ) : (
            messages.map((msg, index) => (
              <div key={index} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'user' ? '👤' : '🤖'}
                </div>
                <div className="message-content">
                  <div className="message-text">
                    {msg.content.split('\n').map((line, i) => (
                      <React.Fragment key={i}>
                        {line}
                        {i < msg.content.split('\n').length - 1 && <br />}
                      </React.Fragment>
                    ))}
                  </div>
                </div>
              </div>
            ))
          )}
          {isLoading && (
            <div className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Area */}
        <div className="input-container">
          <div className="input-wrapper">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Type your message or use voice input..."
              disabled={isLoading}
              rows="1"
            />
            <button
              onClick={handleVoiceInput}
              className={`voice-button ${isRecording ? 'recording' : ''}`}
              disabled={isLoading}
              title={isRecording ? 'Stop recording' : 'Start voice input'}
            >
              {isRecording ? '🔴' : '🎤'}
            </button>
            <button
              onClick={sendMessage}
              disabled={isLoading || !inputValue.trim()}
              className="send-button"
            >
              {isLoading ? '⏳' : '➤'}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
