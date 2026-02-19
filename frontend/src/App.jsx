// ClawForge v4.0 - Full-Screen React Dashboard with Markdown Support
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = '';  // Use proxy - relative to frontend

// Simple Markdown Parser
function parseMarkdown(text) {
  if (!text) return '';
  
  let html = text
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Bold
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    // Lists
    .replace(/^\- (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    // Links
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    // Line breaks
    .replace(/\n/g, '<br>');
  
  return html;
}

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [security, setSecurity] = useState({ mode: 'LOCKED', riskScore: 0 });
  const [loading, setLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { role: 'system', content: "Hello! I'm ClawForge, an advanced AI assistant.\n\nWhat I Can Do:\n- Deep Understanding - complex questions, context retention\n- Reasoning & Analysis - step-by-step problem solving\n- Web Search - Get current information\n- Memory - Remember important things\n- Code - Write and run Python\n- Files - Read and edit files\n- Planning - Create multi-step plans\n\nJust tell me what you need - I'll understand and help!" }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [models, setModels] = useState([
    'z-ai/glm5',
    'qwen/qwen3.5-397b-a17b',
    'NVIDIABuild-Autogen-60',
    'deepseek-ai/deepseek-v3.2',
    'bytedance/seed-oss-36b-instruct'
  ]);
  const [selectedModel, setSelectedModel] = useState('qwen/qwen3.5-397b-a17b');
  const [apiStatus, setApiStatus] = useState({ provider: 'Checking...', status: 'checking' });
  const [memoryStats, setMemoryStats] = useState(null);
  const messagesEndRef = useRef(null);
  const heartbeatRef = useRef(null);
  const reconnectAttempts = useRef(0);

  // Initial load
  useEffect(() => {
    checkApiStatus();
    fetchMemoryStats();
    startHeartbeat();
    return () => stopHeartbeat();
  }, []);

  // Scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [chatMessages]);

  // Heartbeat to keep connection alive
  const startHeartbeat = () => {
    // Heartbeat every 30 seconds to keep connection alive
    heartbeatRef.current = setInterval(async () => {
      try {
        await fetch(`${API_BASE}/api/health`, { 
          method: 'GET',
          cache: 'no-cache'
        });
        if (!isConnected) {
          setIsConnected(true);
          reconnectAttempts.current = 0;
        }
      } catch (e) {
        handleDisconnect();
      }
    }, 30000);
  };

  const stopHeartbeat = () => {
    if (heartbeatRef.current) {
      clearInterval(heartbeatRef.current);
    }
  };

  const handleDisconnect = () => {
    setIsConnected(false);
    if (reconnectAttempts.current < 5) {
      reconnectAttempts.current++;
      setTimeout(() => {
        attemptReconnect();
      }, 5000 * reconnectAttempts.current);
    }
  };

  const attemptReconnect = async () => {
    try {
      await fetch(`${API_BASE}/api/health`, { 
        method: 'GET',
        cache: 'no-cache'
      });
      setIsConnected(true);
      reconnectAttempts.current = 0;
    } catch (e) {
      if (reconnectAttempts.current < 5) {
        setTimeout(() => {
          attemptReconnect();
        }, 5000 * reconnectAttempts.current);
      }
    }
  };

  const checkApiStatus = async () => {
    const apiKey = process.env.NVIDIA_API_KEY || localStorage.getItem('nvidia_api_key');
    if (apiKey) {
      setApiStatus({ provider: 'NVIDIA API', status: 'online' });
    } else {
      setApiStatus({ provider: 'Not Set', status: 'offline' });
    }
  };

  const fetchMemoryStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/longterm-memory/stats`, {
        method: 'GET',
        cache: 'no-cache'
      });
      if (res.ok) {
        const data = await res.json();
        setMemoryStats(data);
      }
    } catch (e) {
      console.log('Long-term memory not available');
    }
  };

  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    if (!isConnected) {
      attemptReconnect();
      return;
    }
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);
    reconnectAttempts.current = 0;

    try {
      let endpoint = '/api/chat';
      if (selectedModel === 'z-ai/glm5') endpoint = '/api/chat/glm5';
      else if (selectedModel === 'qwen/qwen3.5-397b-a17b') endpoint = '/api/chat/qwen';
      
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: `You are ClawForge, a helpful AI assistant. User says: "${userMessage}"` }),
        cache: 'no-cache'
      });

      const data = await res.json();
      
      if (data.status === 'success') {
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.message || 'Error: ' + data.error }]);
      }
    } catch (e) {
      handleDisconnect();
      setChatMessages(prev => [...prev, { role: 'assistant', content: 'Connection lost. Attempting to reconnect...' }]);
    }
    
    setChatLoading(false);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  const tabs = [
    { id: 'chat', label: '💬', title: 'Chat' },
    { id: 'dashboard', label: '📊', title: 'Dashboard' },
    { id: 'prompt', label: '⚡', title: 'Prompt Engine' },
    { id: 'memory', label: '💾', title: 'Memory' },
    { id: 'tasks', label: '📋', title: 'Tasks' },
    { id: 'security', label: '🛡️', title: 'Security' },
    { id: 'tools', label: '🛠️', title: 'Tools' },
  ];

  const renderChat = () => (
    <div className="chat-view">
      {!isConnected && (
        <div className="connection-banner">
          <span>🔄 Reconnecting...</span>
        </div>
      )}
      <div className="chat-header">
        <h2>Chat with ClawForge</h2>
        <p>Powered by {selectedModel.split('/')[1] || selectedModel} via NVIDIA API</p>
      </div>
      
      <div className="chat-messages">
        {chatMessages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div className="message-role">{msg.role === 'system' ? 'ClawForge' : msg.role}</div>
            <div 
              className="message-content" 
              dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }}
            />
          </div>
        ))}
        {chatLoading && (
          <div className="chat-message assistant">
            <div className="message-role">ClawForge</div>
            <div className="typing">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-area">
        <div className="chat-input-wrapper">
          <textarea
            value={chatInput}
            onChange={(e) => setChatInput(e.target.value)}
            onKeyPress={handleKeyPress}
            placeholder="Type your message... (Enter to send)"
            className="chat-input"
            rows={1}
          />
          <button 
            onClick={sendChatMessage} 
            disabled={!chatInput.trim() || chatLoading || !isConnected}
            className="send-btn"
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );

  const renderDashboard = () => (
    <div className="dashboard-view">
      <div className="dashboard-header">
        <h2>Dashboard</h2>
        <p>Your ClawForge overview</p>
      </div>
      <div className="dashboard-grid">
        <div className="dashboard-card">
          <div className="stat">{memoryStats?.total || 0}</div>
          <h3>Total Memories</h3>
          <p>Stored facts and knowledge</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{memoryStats?.session_count || 0}</div>
          <h3>Sessions</h3>
          <p>Conversations remembered</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{memoryStats?.open_tasks || 0}</div>
          <h3>Open Tasks</h3>
          <p>Tasks being tracked</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{security.riskScore || 0}</div>
          <h3>Risk Score</h3>
          <p>Current security level</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{models.length}</div>
          <h3>AI Models</h3>
          <p>Available for chat</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{isConnected ? 'Yes' : 'No'}</div>
          <h3>API Connected</h3>
          <p>{apiStatus.provider}</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{memoryStats?.completed_tasks || 0}</div>
          <h3>Completed Tasks</h3>
          <p>Tasks finished</p>
        </div>
        <div className="dashboard-card">
          <div className="stat">{memoryStats?.total_messages || 0}</div>
          <h3>Total Messages</h3>
          <p>Across all sessions</p>
        </div>
      </div>
    </div>
  );

  const renderContent = () => {
    switch(activeTab) {
      case 'chat': return renderChat();
      case 'dashboard': return renderDashboard();
      default: return (
        <div className="dashboard-view">
          <div className="dashboard-header">
            <h2>{tabs.find(t => t.id === activeTab)?.title}</h2>
            <p>This feature is coming soon!</p>
          </div>
        </div>
      );
    }
  };

  return (
    <div className="app">
      <header className="header">
        <h1>ClawForge v4.0</h1>
        <div className="header-status">
          <select 
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value)}
            className="model-select"
          >
            {models.map(m => (
              <option key={m} value={m}>{m.split('/')[1] || m}</option>
            ))}
          </select>
          <span className={`api-status ${apiStatus.status}`}>
            {apiStatus.provider}
          </span>
          <span className={`risk-badge ${security.riskScore >= 50 ? 'high' : security.riskScore >= 25 ? 'medium' : 'low'}`}>
            Risk: {security.riskScore || 0}
          </span>
          <span className="mode-badge">{security.mode || 'LOCKED'}</span>
        </div>
      </header>

      <nav className="sidebar">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
            title={tab.title}
          >
            {tab.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {renderContent()}
      </main>
    </div>
  );
}

export default App;
