// Leo 2.0 - Full-Screen React Dashboard with NEURON Self-Learning
import React, { useState, useEffect, useRef } from 'react';
import './App.css';

const API_BASE = 'http://127.0.0.1:9000';  // Leo 2.0 Backend

// Simple Markdown Parser
function parseMarkdown(text) {
  if (!text) return '';
  
  let html = text
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em>$1</em>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/^\- (.+)$/gm, '<li>$1</li>')
    .replace(/^\d+\. (.+)$/gm, '<li>$1</li>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener">$1</a>')
    .replace(/\n/g, '<br>');
  
  return html;
}

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [security, setSecurity] = useState({ mode: 'LOCKED', riskScore: 0 });
  const [chatMessages, setChatMessages] = useState([
    { role: 'system', content: "Hello! I'm Leo 2.0, a self-learning AI agent powered by NEURON v2.0.\n\nI learn from every conversation - extracting concepts, building knowledge, and growing smarter over time.\n\nWhat I Can Do:\n- 🧠 Self-Learning - I learn from our conversations\n- 💬 Deep Understanding - complex questions, context retention\n- 🔗 Knowledge Building - I remember what we discuss\n- 📊 Reasoning - step-by-step problem solving\n- 🌐 Web Search - Get current information\n- 💾 Memory - Remember important things\n- 💻 Code - Write and run Python\n- 📁 Files - Read and edit files\n- 🎯 Planning - Create multi-step plans\n\nJust tell me what you need - I'll understand and help!" }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [isConnected, setIsConnected] = useState(true);
  const [models, setModels] = useState([
    'auto',
    'ollama/qwen2.5:3b',
    'ollama/llama3.2:3b',
    'ollama/qwen3:8b',
    'ollama/phi3:mini',
    'z-ai/glm5',
    'qwen/qwen3.5-397b-a17b',
    'NVIDIABuild-Autogen-60',
    'deepseek-ai/deepseek-v3.2',
    'bytedance/seed-oss-36b-instruct'
  ]);
  const [selectedModel, setSelectedModel] = useState('qwen/qwen3.5-397b-a17b');
  const [apiStatus, setApiStatus] = useState({ provider: 'Checking...', status: 'checking' });
  const [memoryStats, setMemoryStats] = useState(null);
  const [ramStats, setRamStats] = useState(null);
  const messagesEndRef = useRef(null);
  const heartbeatRef = useRef(null);
  const reconnectAttempts = useRef(0);

  // Initial load
  useEffect(() => {
    checkApiStatus();
    fetchMemoryStats();
    fetchRamStats();
    startHeartbeat();
    return () => stopHeartbeat();
  }, []);

  // Scroll to bottom - advanced
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ 
        behavior: 'auto',
        block: 'end'
      });
      // Also try native scroll
      const container = document.querySelector('.messages-container');
      if (container) {
        container.scrollTop = container.scrollHeight;
      }
    }
  }, [chatMessages, chatLoading]);

  // Manual scroll handler
  const handleScroll = () => {
    const container = document.querySelector('.messages-container');
    if (container) {
      const { scrollTop, scrollHeight, clientHeight } = container;
      // Auto-scroll if user is near bottom
      if (scrollHeight - scrollTop - clientHeight < 100) {
        container.scrollTop = container.scrollHeight;
      }
    }
  };

  // Heartbeat
  const startHeartbeat = () => {
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
      console.log('Memory stats not available');
    }
  };

  const fetchRamStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/ram`, {
        method: 'GET',
        cache: 'no-cache'
      });
      if (res.ok) {
        const data = await res.json();
        setRamStats(data);
      }
    } catch (e) {
      // RAM info not available
    }
  };

  // Send message with auto-learning
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
      let useSmartRouter = false;
      
      // Use Auto mode (smart router) if selected
      if (selectedModel === 'auto') {
        endpoint = '/api/smart/switch';
        useSmartRouter = true;
      }
      // Use Ollama for local models, NVIDIA for others
      else if (selectedModel.startsWith('ollama/')) {
        endpoint = '/api/chat/ollama';
      } else if (selectedModel === 'z-ai/glm5') {
        endpoint = '/api/chat/glm5';
      } else if (selectedModel === 'qwen/qwen3.5-397b-a17b') {
        endpoint = '/api/chat/qwen';
      }
      
      // Create abort controller for timeout (2 minutes)
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 120000);
      
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message: userMessage }),
        cache: 'no-cache',
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      const data = await res.json();
      
      if (data.status === 'success') {
        let responseText = typeof data.response === 'string' ? data.response : JSON.stringify(data.response);
        let modelNote = '';
        
        if (useSmartRouter && data.model_used) {
          const modelName = data.model_used.replace('ollama/', '');
          modelNote = `\n\n🤖 *Auto-selected model: ${modelName}*`;
        }
        
        setChatMessages(prev => [...prev, { role: 'assistant', content: responseText + modelNote }]);
        triggerAutoLearn(userMessage);
      } else {
        let errorMsg = typeof data.message === 'string' ? data.message : JSON.stringify(data.message || data.error || 'Unknown error');
        setChatMessages(prev => [...prev, { role: 'assistant', content: 'Error: ' + errorMsg }]);
      }
    } catch (e) {
      if (e.name === 'AbortError') {
        setChatMessages(prev => [...prev, { role: 'assistant', content: '⏳ This is taking longer than expected. Please wait...' }]);
      } else {
        handleDisconnect();
        setChatMessages(prev => [...prev, { role: 'assistant', content: 'Connection lost. Attempting to reconnect...' }]);
      }
    } finally {
      setChatLoading(false);
    }
  };

  // Auto-learning trigger - learns silently from every conversation
  const triggerAutoLearn = async (userInput) => {
    try {
      await fetch(`${API_BASE}/api/neuron/learn`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          user_input: userInput,
          strategy: 'Synthesis'
        }),
      });
      // Learning happens silently in background
    } catch (e) {
      // Silent fail - learning is optional
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendChatMessage();
    }
  };

  const handleFileUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    
    // Check file size (5MB limit)
    const maxSize = 5 * 1024 * 1024; // 5MB
    if (file.size > maxSize) {
      setChatMessages(prev => [...prev, { 
        role: 'system', 
        content: `❌ File too large! Maximum size is 5MB. Your file is ${(file.size / 1024 / 1024).toFixed(2)}MB` 
      }]);
      e.target.value = '';
      return;
    }
    
    // Check file type
    const allowedTypes = [
      'text/plain', 'text/markdown', 'text/html', 'text/css', 'text/javascript',
      'application/json', 'application/javascript',
      'application/pdf', 'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    
    const ext = file.name.split('.').pop().toLowerCase();
    const allowedExts = ['txt', 'md', 'json', 'js', 'py', 'html', 'css', 'xml', 'csv', 'pdf', 'doc', 'docx'];
    
    if (!allowedExts.includes(ext)) {
      setChatMessages(prev => [...prev, { 
        role: 'system', 
        content: `❌ File type not supported! Allowed: ${allowedExts.join(', ')}` 
      }]);
      e.target.value = '';
      return;
    }
    
    // Show uploading message
    setChatMessages(prev => [...prev, { 
      role: 'system', 
      content: `📤 Uploading "${file.name}"... (${(file.size / 1024).toFixed(1)}KB)` 
    }]);
    
    // For PDF and DOC, we need special handling
    if (ext === 'pdf' || ext === 'doc' || ext === 'docx') {
      // Send file as base64 for special processing
      const reader = new FileReader();
      reader.onload = async () => {
        const base64 = reader.result.split(',')[1];
        
        try {
          const response = await fetch(`${API_BASE}/api/rag/document/add`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
              content: base64,
              source: file.name,
              is_base64: true,
              file_type: ext,
              metadata: {
                type: file.type,
                size: file.size,
                uploaded: new Date().toISOString()
              }
            }),
          });
          
          const result = await response.json();
          
          if (result.status === 'ok') {
            setChatMessages(prev => [...prev, { 
              role: 'system', 
              content: `📎 File "${file.name}" uploaded successfully! (${(file.size / 1024).toFixed(1)}KB)` 
            }]);
          } else {
            setChatMessages(prev => [...prev, { 
              role: 'system', 
              content: `❌ Upload failed: ${result.error || 'Unknown error'}` 
            }]);
          }
        } catch (err) {
          setChatMessages(prev => [...prev, { 
            role: 'system', 
            content: `❌ Upload error: ${err.message}` 
          }]);
        }
      };
      
      reader.readAsDataURL(file);
      e.target.value = '';
      return;
    }
    
    // For text files, read as text
    const reader = new FileReader();
    reader.onload = async (event) => {
      const content = event.target.result;
      
      try {
        const response = await fetch(`${API_BASE}/api/rag/document/add`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            content: content.substring(0, 5000000), // Limit to 5MB chars
            source: file.name,
            metadata: {
              type: file.type,
              size: file.size,
              uploaded: new Date().toISOString()
            }
          }),
        });
        
        const result = await response.json();
        
        if (result.status === 'ok') {
          setChatMessages(prev => [...prev, { 
            role: 'system', 
            content: `📎 File "${file.name}" uploaded successfully! (${(file.size / 1024).toFixed(1)}KB)` 
          }]);
        } else {
          setChatMessages(prev => [...prev, { 
            role: 'system', 
            content: `❌ Upload failed: ${result.error || 'Unknown error'}` 
          }]);
        }
      } catch (err) {
        setChatMessages(prev => [...prev, { 
          role: 'system', 
          content: `❌ Upload error: ${err.message}` 
        }]);
      }
    };
    
    reader.onerror = () => {
      setChatMessages(prev => [...prev, { 
        role: 'system', 
        content: `❌ Error reading file` 
      }]);
    };
    
    reader.readAsText(file);
    e.target.value = '';
  };

  const tabs = [
    { id: 'chat', label: '💬', title: 'Chat' },
    { id: 'memory', label: '💾', title: 'Memory' },
    { id: 'rag', label: '📚', title: 'Knowledge' },
    { id: 'security', label: '🛡️', title: 'Security' },
    { id: 'browser', label: '🌐', title: 'Browser' },
    { id: 'code', label: '💻', title: 'Code' },
    { id: 'files', label: '📁', title: 'Files' },
    { id: 'settings', label: '⚙️', title: 'Settings' },
  ];

  const renderChat = () => (
    <div className="chat-view">
      {!isConnected && (
        <div className="connection-banner">
          <span>🔄 Reconnecting...</span>
        </div>
      )}
      <div className="chat-header">
        <h2>Chat with Leo 2.0</h2>
        <p>Powered by {selectedModel.split('/')[1] || selectedModel} • Self-learning via NEURON v2.0</p>
      </div>
      
      <div className="chat-messages" onScroll={handleScroll}>
        {chatMessages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div className="message-role">{msg.role === 'system' ? 'Leo 2.0' : msg.role}</div>
            <div 
              className="message-content" 
              dangerouslySetInnerHTML={{ __html: parseMarkdown(msg.content) }}
            />
          </div>
        ))}
        {chatLoading && (
          <div className="chat-message assistant">
            <div className="message-role">Leo 2.0</div>
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
          <input
            type="file"
            id="file-upload"
            style={{ display: 'none' }}
            onChange={handleFileUpload}
            accept=".txt,.pdf,.md,.json,.py,.js,.html,.css,.csv,.doc,.docx"
          />
          <button 
            className="upload-btn"
            onClick={() => document.getElementById('file-upload').click()}
            title="Upload document to knowledge base (max 5MB)"
          >
            📎
          </button>
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
        <p>Your Leo 2.0 overview • Powered by NEURON v2.0</p>
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
        <div className="dashboard-card ram-card">
          <div className="stat" style={{ color: ramStats?.percent_used > 80 ? '#ff6b6b' : '#51cf66' }}>
            {ramStats?.used_gb || 0}GB / {ramStats?.total_gb || 0}GB
          </div>
          <h3>RAM Usage</h3>
          <p>{ramStats?.percent_used || 0}% {ramStats?.percent_used > 80 ? '⚠️ High' : '✅ OK'}</p>
          <button 
            className="clean-ram-btn"
            onClick={async () => {
              await fetch(`${API_BASE}/api/memory/cleanup?type=full`, { method: 'POST' });
              fetchRamStats();
            }}
          >
            🧹 Clean RAM
          </button>
        </div>
        <div className="dashboard-card smart-router-card">
          <div className="stat">🤖</div>
          <h3>Smart Router</h3>
          <p>{selectedModel === 'auto' ? '✅ Auto Mode Active' : '❌ Manual Mode'}</p>
          {selectedModel === 'auto' && (
            <button 
              className="clean-ram-btn"
              onClick={async () => {
                try {
                  const res = await fetch(`${API_BASE}/api/smart/stats`, { method: 'GET' });
                  const data = await res.json();
                  if (data.statistics) {
                    alert(`Smart Router Stats:\n\nCurrent Model: ${data.current_model}\nTotal Analyses: ${data.statistics.total_analyses}\nTotal Switches: ${data.statistics.total_switches}\nSwitch Rate: ${data.statistics.switch_rate}%`);
                  }
                } catch (e) {
                  console.log('Smart stats not available');
                }
              }}
            >
              📊 View Stats
            </button>
          )}
        </div>
      </div>
    </div>
  );

  // Placeholder functions for new tabs - defined before use

  const renderRag = () => (
    <div className="rag-view">
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--neon-blue)' }}>📚 Knowledge Base</h2>
      <div className="rag-stats">
        <div className="stat-box">
          <div className="stat-value">0</div>
          <div className="stat-label">Documents</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">0</div>
          <div className="stat-label">Chunks</div>
        </div>
        <div className="stat-box">
          <div className="stat-value">0</div>
          <div className="stat-label">Searches</div>
        </div>
      </div>
      <button className="btn btn-primary" style={{ marginRight: '1rem' }}>+ Add Document</button>
      <button className="btn btn-secondary">🔍 Search</button>
    </div>
  );

  const renderBrowser = () => (
    <div className="browser-view">
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--neon-blue)' }}>🌐 Browser Automation</h2>
      <p>Browser automation API available at /api/browser/*</p>
    </div>
  );

  const renderCode = () => (
    <div className="code-view">
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--neon-blue)' }}>💻 Code Interpreter</h2>
      <p>Python code execution API available at /api/code/*</p>
    </div>
  );

  const renderFiles = () => (
    <div className="files-view">
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--neon-blue)' }}>📁 File System</h2>
      <p>File operations API available at /api/files/*</p>
    </div>
  );

  const renderSecurity = () => (
    <div className="settings-view">
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--neon-blue)' }}>🛡️ Security</h2>
      <div className="settings-section">
        <div className="settings-title">Security Status</div>
        <p style={{ color: '#51cf66', fontSize: '1.2rem', marginBottom: '1rem' }}>
          ✅ Protected
        </p>
        <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
          <span style={{ padding: '0.4rem 0.8rem', background: 'rgba(0,212,255,0.2)', borderRadius: '6px', fontSize: '0.85rem' }}>
            🛡️ Custodian Active
          </span>
          <span style={{ padding: '0.4rem 0.8rem', background: 'rgba(0,212,255,0.2)', borderRadius: '6px', fontSize: '0.85rem' }}>
            🔒 Privacy First
          </span>
          <span style={{ padding: '0.4rem 0.8rem', background: 'rgba(0,212,255,0.2)', borderRadius: '6px', fontSize: '0.85rem' }}>
            📝 Audit Logging
          </span>
        </div>
      </div>
      <div className="settings-section">
        <div className="settings-title">Risk Score</div>
        <p style={{ fontSize: '2rem', color: security.riskScore < 50 ? '#51cf66' : '#ff6b6b' }}>
          {security.riskScore || 0}%
        </p>
        <p style={{ color: 'var(--text-secondary)', fontSize: '0.9rem' }}>
          {security.riskScore < 30 ? 'Low risk - All systems secure' : security.riskScore < 70 ? 'Medium risk - Monitor activities' : 'High risk - Review required'}
        </p>
      </div>
      <div className="settings-section">
        <div className="settings-title">Data Protection</div>
        <p style={{ color: 'var(--text-secondary)', marginBottom: '0.5rem' }}>
          • All data stored locally<br/>
          • No personal data collection<br/>
          • Request monitoring enabled<br/>
          • External threats blocked
        </p>
      </div>
    </div>
  );




  const renderSettings = () => (
    <div className="settings-view">
      <h2 style={{ marginBottom: '1.5rem', color: 'var(--neon-blue)' }}>⚙️ Settings</h2>
      <div className="settings-section">
        <div className="settings-title">Model Selection</div>
        <select 
          value={selectedModel} 
          onChange={(e) => setSelectedModel(e.target.value)}
          style={{ 
            width: '100%', 
            padding: '0.75rem', 
            background: 'rgba(0,0,0,0.5)', 
            border: '1px solid var(--border-color)',
            borderRadius: '8px',
            color: 'var(--text-primary)',
            fontSize: '1rem'
          }}
        >
          {models.map(m => (
            <option key={m} value={m}>{m}</option>
          ))}
        </select>
      </div>
      <div className="settings-section">
        <div className="settings-title">Connection Status</div>
        <p style={{ color: isConnected ? '#51cf66' : '#ff6b6b' }}>
          {isConnected ? '✅ Connected' : '❌ Disconnected'}
        </p>
      </div>
    </div>
  );

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="app-logo">
          🦁 <span>LEO 2.0</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <select 
            value={selectedModel} 
            onChange={(e) => setSelectedModel(e.target.value)}
            style={{ 
              padding: '0.5rem 1rem', 
              background: 'rgba(0,0,0,0.5)', 
              border: '1px solid var(--neon-blue)',
              borderRadius: '8px',
              color: 'var(--neon-blue)',
              fontSize: '0.9rem',
              cursor: 'pointer'
            }}
          >
            {models.map(m => (
              <option key={m} value={m}>
                {m === 'auto' ? '🤖 Auto' : (m.split('/')[1] || m)}
              </option>
            ))}
          </select>
        </div>
      </header>

      <nav className="tab-bar">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.label} {tab.title}
          </button>
        ))}
      </nav>

      <main className="main">
        {activeTab === 'browser' && <div style={{padding:'2rem'}}><h2>Browser</h2><p>Click Start Browser to begin</p></div>}
        {activeTab === 'code' && <div style={{padding:'2rem'}}><h2>Code</h2><p>Write and run Python</p></div>}
        {activeTab === 'files' && <div style={{padding:'2rem'}}><h2>Files</h2><p>Browse files</p></div>}
        {(activeTab === 'chat' || activeTab === 'memory' || activeTab === 'rag' || activeTab === 'security' || activeTab === 'settings') && renderContent()}
      </main>
    </div>
  );
}

export default App;
