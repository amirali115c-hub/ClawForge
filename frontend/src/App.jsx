// ClawForge v4.0 - React Dashboard
import React, { useState, useEffect, useRef } from 'react';
import './App.css';
import './memory_styles.css';

const API_BASE = 'http://127.0.0.1:8000';

function App() {
  const [activeTab, setActiveTab] = useState('chat');
  const [tasks, setTasks] = useState([]);
  const [security, setSecurity] = useState({ mode: 'LOCKED', riskScore: 0 });
  const [newTask, setNewTask] = useState('');
  const [loading, setLoading] = useState(false);
  const [chatMessages, setChatMessages] = useState([
    { role: 'system', content: "Hello! I'm ClawForge, an advanced AI assistant.\n\n**What I Can Do:**\n\n🔍 Deep Understanding\n- Understand complex, multi-part questions\n- Remember context from our entire conversation\n- Extract your real intent from natural language\n\n🧠 Reasoning & Analysis\n- Break down complex problems step-by-step\n- Consider multiple perspectives\n- Explain my reasoning when helpful\n\n🔧 My Tools\n- 🌐 Web Search - Get current information\n- 💾 Memory - Remember important things\n- 💻 Code - Write and run Python\n- 📁 Files - Read and edit files\n- 📝 Planning - Create multi-step plans\n\nJust tell me what you need - I'll understand and help!" }
  ]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [models, setModels] = useState([]);
  const [selectedModel, setSelectedModel] = useState('qwen/qwen3.5-397b-a17b');
  const [apiStatus, setApiStatus] = useState({ provider: 'Checking...', status: 'checking' });
  const [memoryStats, setMemoryStats] = useState(null);
  const [memories, setMemories] = useState([]);
  const [conversations, setConversations] = useState([]);
  const [privacySettings, setPrivacySettings] = useState(null);
  const [gitStatus, setGitStatus] = useState(null);
  const [searchResults, setSearchResults] = useState([]);
  const [planResult, setPlanResult] = useState(null);
  const [ttsResult, setTtsResult] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [planGoal, setPlanGoal] = useState('');
  const [ttsText, setTtsText] = useState('');
  const [featureLoading, setFeatureLoading] = useState(false);

  useEffect(() => {
    fetchData();
    fetchModels();
    checkApiStatus();
  }, []);

  const checkApiStatus = async () => {
    const apiKey = process.env.NVIDIA_API_KEY || localStorage.getItem('nvidia_api_key');
    if (apiKey) {
      setApiStatus({ provider: 'NVIDIA API', status: 'online' });
    } else {
      setApiStatus({ provider: 'Not Set', status: 'offline' });
    }
  };

  const fetchModels = async () => {
    // Five models available
    setModels([
      'z-ai/glm5',
      'qwen/qwen3.5-397b-a17b',
      'NVIDIABuild-Autogen-60',
      'deepseek-ai/deepseek-v3.2',
      'bytedance/seed-oss-36b-instruct'
    ]);
    setSelectedModel('z-ai/glm5');
  };

  const fetchData = async () => {
    try {
      const [tasksRes, securityRes] = await Promise.all([
        fetch(`${API_BASE}/api/tasks`),
        fetch(`${API_BASE}/api/security`)
      ]);
      
      if (tasksRes.ok) {
        const data = await tasksRes.json();
        setTasks(data.tasks || []);
      }
      if (securityRes.ok) {
        setSecurity(await securityRes.json());
      }
    } catch (e) {
      console.log('API not available yet');
    }
  };

  // Chat function - uses API endpoint based on model
  const sendChatMessage = async () => {
    if (!chatInput.trim() || chatLoading) return;
    
    const userMessage = chatInput.trim();
    setChatInput('');
    setChatMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setChatLoading(true);

    try {
      // Choose endpoint based on model
      let endpoint = '/api/chat';
      if (selectedModel === 'z-ai/glm5') endpoint = '/api/chat/glm5';
      else if (selectedModel === 'qwen/qwen3.5-397b-a17b') endpoint = '/api/chat/qwen';
      else if (selectedModel === 'NVIDIABuild-Autogen-60') endpoint = '/api/chat/nvidia-build';
      else if (selectedModel === 'deepseek-ai/deepseek-v3.2') endpoint = '/api/chat/deepseek';
      else if (selectedModel === 'bytedance/seed-oss-36b-instruct') endpoint = '/api/chat/bytedance';
      
      const res = await fetch(`${API_BASE}${endpoint}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: `You are ClawForge, a helpful AI assistant. User says: "${userMessage}"`
        })
      });

      const data = await res.json();
      
      if (data.status === 'success') {
        setChatMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
      } else {
        setChatMessages(prev => [...prev, { 
          role: 'assistant', 
          content: data.message || 'Error: ' + data.error 
        }]);
      }
    } catch (e) {
      setChatMessages(prev => [...prev, { 
        role: 'assistant', 
        content: 'Sorry, I could not connect to the API. Make sure your API key is set.' 
      }]);
    }
    
    setChatLoading(false);
  };

  const createTask = async () => {
    if (!newTask.trim()) return;
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/tasks`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: newTask, category: 'general' })
      });
      if (res.ok) {
        setNewTask('');
        fetchData();
      }
    } catch (e) {
      alert('Failed to create task');
    }
    setLoading(false);
  };

  const executeTask = async (taskId) => {
    setLoading(true);
    try {
      await fetch(`${API_BASE}/api/tasks/${taskId}/start`, { method: 'POST' });
      fetchData();
    } catch (e) {
      alert('Failed to execute task');
    }
    setLoading(false);
  };

  const killTask = async (taskId) => {
    try {
      await fetch(`${API_BASE}/api/tasks/${taskId}/cancel`, { method: 'POST' });
      fetchData();
    } catch (e) {
      alert('Failed to kill task');
    }
  };

  // Feature functions
  const fetchMemoryStats = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/stats`);
      if (res.ok) setMemoryStats(await res.json());
    } catch (e) {
      console.log('Failed to fetch memory stats');
    }
  };

  // Long-term memory functions
  const loadMemories = async (category = null) => {
    try {
      const url = category 
        ? `${API_BASE}/api/memory/all?category=${category}`
        : `${API_BASE}/api/memory/all`;
      const res = await fetch(url);
      if (res.ok) {
        const data = await res.json();
        setMemories(data.memories || []);
      }
    } catch (e) {
      console.log('Failed to load memories');
    }
  };

  const addMemory = async (memory) => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/add`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(memory)
      });
      if (res.ok) {
        fetchMemoryStats();
        loadMemories();
      }
    } catch (e) {
      console.log('Failed to add memory');
    }
  };

  const deleteMemory = async (id) => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/${id}`, { method: 'DELETE' });
      if (res.ok) {
        fetchMemoryStats();
        loadMemories();
      }
    } catch (e) {
      console.log('Failed to delete memory');
    }
  };

  const clearCategory = async (category) => {
    if (!confirm(`Clear all ${category} memories?`)) return;
    try {
      const res = await fetch(`${API_BASE}/api/memory/category/${category}`, { method: 'DELETE' });
      if (res.ok) {
        fetchMemoryStats();
        loadMemories();
      }
    } catch (e) {
      console.log('Failed to clear category');
    }
  };

  const loadConversations = async (limit = 50) => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/conversations?limit=${limit}`);
      if (res.ok) {
        const data = await res.json();
        setConversations(data.conversations || []);
      }
    } catch (e) {
      console.log('Failed to load conversations');
    }
  };

  const clearConversations = async () => {
    if (!confirm('Clear all conversations?')) return;
    try {
      await fetch(`${API_BASE}/api/memory/conversations/clear`, { method: 'DELETE' });
      setConversations([]);
    } catch (e) {
      console.log('Failed to clear conversations');
    }
  };

  const loadPrivacySettings = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/privacy`);
      if (res.ok) setPrivacySettings(await res.json());
    } catch (e) {
      console.log('Failed to load privacy settings');
    }
  };

  const updatePrivacySettings = async (settings) => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/privacy`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(settings)
      });
      if (res.ok) loadPrivacySettings();
    } catch (e) {
      console.log('Failed to update privacy settings');
    }
  };

  const exportMemory = (includeSensitive = false) => {
    // This returns data synchronously for download
    fetch(`${API_BASE}/api/memory/export?include_sensitive=${includeSensitive}`)
      .then(res => res.json())
      .then(data => {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `clawforge_memory_${new Date().toISOString().split('T')[0]}.json`;
        a.click();
      });
    return {}; // Return empty for now
  };

  const importMemoryData = async (data) => {
    try {
      const res = await fetch(`${API_BASE}/api/memory/import`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ ...data, merge: true })
      });
      return await res.json();
    } catch (e) {
      console.log('Failed to import memory');
      return { error: 'Failed' };
    }
  };

  const fetchGitStatus = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/git/status`);
      if (res.ok) setGitStatus(await res.json());
    } catch (e) {
      console.log('Failed to fetch git status');
    }
  };

  const handleWebSearch = async () => {
    if (!searchQuery.trim()) return;
    setFeatureLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/search`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query: searchQuery, num_results: 10 })
      });
      if (res.ok) {
        const data = await res.json();
        setSearchResults(data.results || []);
      }
    } catch (e) {
      setSearchResults([{ title: 'Error', snippet: 'Search failed' }]);
    }
    setFeatureLoading(false);
  };

  const handleGeneratePlan = async () => {
    if (!planGoal.trim()) return;
    setFeatureLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/plans/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goal: planGoal })
      });
      if (res.ok) setPlanResult(await res.json());
    } catch (e) {
      setPlanResult({ goal: 'Error', steps: [] });
    }
    setFeatureLoading(false);
  };

  const handleTTS = async () => {
    if (!ttsText.trim()) return;
    setFeatureLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/tts/speak`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: ttsText })
      });
      if (res.ok) setTtsResult(await res.json());
    } catch (e) {
      setTtsResult({ status: 'error', message: 'TTS failed' });
    }
    setFeatureLoading(false);
  };

  const tabs = [
    { id: 'chat', label: 'Chat', icon: 'C' },
    { id: 'dashboard', label: 'Dashboard', icon: 'D' },
    { id: 'tasks', label: 'Tasks', icon: 'T' },
    { id: 'memory', label: 'Memory', icon: 'M' },
    { id: 'features', label: 'Features', icon: 'F' },
    { id: 'tools', label: 'Tools', icon: 'O' },
    { id: 'security', label: 'Security', icon: 'S' },
  ];

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
              <option key={m} value={m}>{m}</option>
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

      <nav className="nav">
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`nav-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {activeTab === 'chat' && (
          <ChatView 
            messages={chatMessages}
            input={chatInput}
            setInput={setChatInput}
            onSend={sendChatMessage}
            loading={chatLoading}
          />
        )}
        
        {activeTab === 'dashboard' && (
          <DashboardView 
            tasks={tasks} 
            security={security}
            onExecute={executeTask}
            onKill={killTask}
          />
        )}
        
        {activeTab === 'tasks' && (
          <TasksView
            tasks={tasks}
            newTask={newTask}
            setNewTask={setNewTask}
            onCreate={createTask}
            onExecute={executeTask}
            onKill={killTask}
            loading={loading}
          />
        )}
        
        {activeTab === 'memory' && (
          <MemoryView
            memoryStats={memoryStats}
            onRefreshStats={fetchMemoryStats}
            memories={memories}
            onLoadMemories={loadMemories}
            privacySettings={privacySettings}
            onLoadPrivacy={loadPrivacySettings}
            onAddMemory={addMemory}
            onDeleteMemory={deleteMemory}
            onClearCategory={clearCategory}
            conversations={conversations}
            onLoadConversations={loadConversations}
            onClearConversations={clearConversations}
            onExport={exportMemory}
            onImport={importMemoryData}
            onUpdatePrivacy={updatePrivacySettings}
          />
        )}
        
        {activeTab === 'tools' && <ToolsView />}
        
        {activeTab === 'security' && <SecurityView security={security} />}
      </main>
    </div>
  );
}

function ChatView({ messages, input, setInput, onSend, loading }) {
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      onSend();
    }
  };

  return (
    <div className="chat-view">
      <div className="chat-header">
        <h2>Chat with ClawForge</h2>
        <p>Powered by Qwen3.5-397B via NVIDIA API</p>
      </div>
      
      <div className="chat-messages">
        {messages.map((msg, i) => (
          <div key={i} className={`chat-message ${msg.role}`}>
            <div className="message-role">{msg.role === 'system' ? 'ClawForge' : msg.role}</div>
            <div className="message-content">{msg.content}</div>
          </div>
        ))}
        {loading && (
          <div className="chat-message assistant">
            <div className="message-role">ClawForge</div>
            <div className="message-content typing">
              <span>.</span><span>.</span><span>.</span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      
      <div className="chat-input-area">
        <textarea
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message... (Enter to send)"
          className="chat-input"
          rows={2}
        />
        <button 
          onClick={onSend} 
          disabled={loading || !input.trim()}
          className="chat-send-btn"
        >
          Send
        </button>
      </div>
    </div>
  );
}

function DashboardView({ tasks, security, onExecute, onKill }) {
  const running = tasks.filter(t => t.status === 'RUNNING').length;
  const completed = tasks.filter(t => t.status === 'COMPLETED').length;

  return (
    <div className="dashboard">
      <div className="stats-grid">
        <div className="stat-card">
          <h3>Total Tasks</h3>
          <div className="stat-value">{tasks.length}</div>
        </div>
        <div className="stat-card running">
          <h3>Running</h3>
          <div className="stat-value">{running}</div>
        </div>
        <div className="stat-card completed">
          <h3>Completed</h3>
          <div className="stat-value">{completed}</div>
        </div>
      </div>

      <div className="recent-tasks">
        <h3>Recent Tasks</h3>
        {tasks.slice(-5).reverse().map(task => (
          <div key={task.task_id} className={`task-item ${(task.status || '').toLowerCase()}`}>
            <span className="task-id">{task.task_id}</span>
            <span className="task-desc">{(task.goal || '').substring(0, 40)}...</span>
            <span className={`status-badge ${(task.status || '').toLowerCase()}`}>{task.status}</span>
          </div>
        ))}
      </div>
    </div>
  );
}

function TasksView({ tasks, newTask, setNewTask, onCreate, onExecute, onKill, loading }) {
  return (
    <div className="tasks-view">
      <div className="create-task">
        <h3>Create New Task</h3>
        <div className="input-group">
          <input
            type="text"
            value={newTask}
            onChange={(e) => setNewTask(e.target.value)}
            placeholder="Describe your task..."
            className="task-input"
          />
          <button onClick={onCreate} disabled={loading} className="create-btn">
            {loading ? 'Creating...' : 'Create Task'}
          </button>
        </div>
      </div>

      <div className="task-list">
        {tasks.map(task => (
          <div key={task.task_id} className={`task-card ${(task.status || '').toLowerCase()}`}>
            <div className="task-header">
              <span className="task-id">{task.task_id}</span>
              <span className={`status-badge ${(task.status || '').toLowerCase()}`}>{task.status}</span>
            </div>
            <p className="task-desc">{task.goal}</p>
            <div className="task-actions">
              {task.status === 'PLANNED' && (
                <button onClick={() => onExecute(task.task_id)} className="btn-primary">Execute</button>
              )}
              {task.status === 'RUNNING' && (
                <button onClick={() => onKill(task.task_id)} className="btn-danger">Cancel</button>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ToolsView() {
  const tools = [
    { category: 'File', tools: ['read_file', 'write_file', 'move_file', 'delete_file'] },
    { category: 'Terminal', tools: ['run_command', 'list_processes'] },
    { category: 'Browser', tools: ['open_url', 'extract_text'] },
    { category: 'Code', tools: ['run_python', 'run_node', 'lint_code'] },
  ];

  return (
    <div className="tools-view">
      <h2>Available Tools</h2>
      <div className="tools-grid">
        {tools.map(group => (
          <div key={group.category} className="tool-group">
            <h3>{group.category}</h3>
            <ul>
              {group.tools.map(tool => (
                <li key={tool}>{tool}</li>
              ))}
            </ul>
          </div>
        ))}
      </div>
    </div>
  );
}

function SecurityView({ security }) {
  return (
    <div className="security-view">
      <h2>Security Dashboard</h2>
      
      <div className="security-card">
        <h3>Security Mode</h3>
        <div className="mode-selector">
          {['LOCKED', 'SAFE', 'DEVELOPER'].map(mode => (
            <button 
              key={mode}
              className={`mode-btn ${security.mode === mode ? 'active' : ''}`}
            >
              {mode}
            </button>
          ))}
        </div>
        <p>LOCKED: Maximum security. All risky actions require approval.</p>
      </div>

      <div className="security-card">
        <h3>Risk Score</h3>
        <div className="risk-display">
          <div className="risk-number">{security.riskScore || 0}</div>
        </div>
      </div>
    </div>
  );
}

function FeaturesView({ 
  memoryStats, gitStatus, searchResults, planResult, ttsResult,
  searchQuery, setSearchQuery, planGoal, setPlanGoal, ttsText, setTtsText,
  onSearch, onPlan, onTTS, onMemory, onGit, loading 
}) {
  return (
    <div className="features-view">
      <h2>AI Features</h2>
      
      <div className="features-grid">
        {/* Memory Card */}
        <div className="feature-card">
          <h3>Memory System</h3>
          <button onClick={onMemory} disabled={loading}>Refresh Stats</button>
          {memoryStats && (
            <div className="feature-stats">
              <p>Conversations: {memoryStats.total_conversations || 0}</p>
              <p>Messages: {memoryStats.total_messages || 0}</p>
              <p>Last Saved: {memoryStats.last_saved?.split('T')[0]}</p>
            </div>
          )}
        </div>

        {/* Git Card */}
        <div className="feature-card">
          <h3>Git Integration</h3>
          <button onClick={onGit} disabled={loading}>Check Status</button>
          {gitStatus && (
            <div className="feature-stats">
              <p>Branch: {gitStatus.branch}</p>
              <p>Has Changes: {gitStatus.has_changes ? 'Yes' : 'No'}</p>
              {gitStatus.changed_files?.length > 0 && (
                <ul className="file-list">
                  {gitStatus.changed_files.slice(0, 3).map((f, i) => (
                    <li key={i}>{f}</li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* Web Search Card */}
        <div className="feature-card">
          <h3>Web Search</h3>
          <div className="feature-input">
            <input 
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search query..."
            />
            <button onClick={onSearch} disabled={loading}>Search</button>
          </div>
          {searchResults.length > 0 && (
            <div className="search-results">
              {searchResults.slice(0, 3).map((r, i) => (
                <div key={i} className="result-item">
                  <p><strong>{r.title}</strong></p>
                  <p>{r.snippet?.substring(0, 100)}...</p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Planner Card */}
        <div className="feature-card">
          <h3>Task Planner</h3>
          <div className="feature-input">
            <input 
              value={planGoal}
              onChange={(e) => setPlanGoal(e.target.value)}
              placeholder="Goal (e.g., Write a blog post)..."
            />
            <button onClick={onPlan} disabled={loading}>Generate Plan</button>
          </div>
          {planResult && (
            <div className="plan-result">
              <p><strong>Goal:</strong> {planResult.goal}</p>
              <p><strong>Steps:</strong> {planResult.total_steps}</p>
              <ol>
                {planResult.steps?.slice(0, 3).map((s, i) => (
                  <li key={i}>{s.description}</li>
                ))}
              </ol>
            </div>
          )}
        </div>

        {/* TTS Card */}
        <div className="feature-card">
          <h3>Text-to-Speech</h3>
          <div className="feature-input">
            <textarea 
              value={ttsText}
              onChange={(e) => setTtsText(e.target.value)}
              placeholder="Enter text to speak..."
              rows={2}
            />
            <button onClick={onTTS} disabled={loading}>Speak</button>
          </div>
          {ttsResult && (
            <div className="tts-result">
              {ttsResult.status === 'success' ? (
                <p>Generated: {ttsResult.filename}</p>
              ) : (
                <p>Error: {ttsResult.message}</p>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// ============================================================================
// LONG-TERM MEMORY VIEW
// ============================================================================

function MemoryView({ 
  memoryStats, onRefreshStats,
  memories, onLoadMemories,
  privacySettings, onLoadPrivacy,
  onAddMemory, onDeleteMemory, onClearCategory,
  conversations, onLoadConversations,
  onClearConversations, onExport, onImport,
  onUpdatePrivacy
}) {
  const [activeTab, setActiveTab] = useState('memories');
  const [newMemory, setNewMemory] = useState({ content: '', category: 'fact', importance: 5, tags: '' });
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [importData, setImportData] = useState('');

  const categories = [
    { id: 'fact', name: 'Facts & Knowledge', icon: '📚' },
    { id: 'preference', name: 'Preferences', icon: '⚙️' },
    { id: 'context', name: 'Project Context', icon: '📁' },
    { id: 'personal', name: 'Personal', icon: '👤' },
    { id: 'setting', name: 'Settings', icon: '🔧' }
  ];

  const handleAddMemory = () => {
    if (!newMemory.content.trim()) return;
    const tags = newMemory.tags.split(',').map(t => t.trim()).filter(t => t);
    onAddMemory({
      content: newMemory.content,
      category: newMemory.category,
      importance: newMemory.importance,
      tags
    });
    setNewMemory({ content: '', category: 'fact', importance: 5, tags: '' });
  };

  const handleSearch = () => {
    if (!searchQuery.trim()) return;
    const results = memories.filter(m => 
      m.content.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.tags?.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()))
    );
    setSearchResults(results);
  };

  const handleExport = () => {
    const data = onExport(false);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `clawforge_memory_${new Date().toISOString().split('T')[0]}.json`;
    a.click();
  };

  const handleImport = () => {
    try {
      const data = JSON.parse(importData);
      onImport(data);
      setImportData('');
      alert('Memory imported successfully!');
    } catch (e) {
      alert('Invalid JSON format');
    }
  };

  return (
    <div className="memory-view">
      <h2>Long-Term Memory</h2>
      
      {/* Stats Bar */}
      <div className="memory-stats-bar">
        <div className="stat-item">
          <span className="stat-number">{memoryStats?.total_memories || 0}</span>
          <span className="stat-label">Total Memories</span>
        </div>
        <div className="stat-item">
          <span className="stat-number">{memoryStats?.total_conversations || 0}</span>
          <span className="stat-label">Conversations</span>
        </div>
        <button onClick={onRefreshStats} className="refresh-btn">Refresh</button>
      </div>

      {/* Tabs */}
      <div className="memory-tabs">
        {['memories', 'add', 'conversations', 'privacy', 'settings'].map(tab => (
          <button
            key={tab}
            className={`tab-btn ${activeTab === tab ? 'active' : ''}`}
            onClick={() => setActiveTab(tab)}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="memory-content">
        
        {/* Memories Tab */}
        {activeTab === 'memories' && (
          <div className="memories-tab">
            <div className="search-box">
              <input 
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search memories..."
              />
              <button onClick={handleSearch}>Search</button>
            </div>

            {searchResults.length > 0 ? (
              <div className="memory-list">
                {searchResults.map((mem, i) => (
                  <div key={i} className="memory-item">
                    <div className="memory-header">
                      <span className="category-badge">{categories.find(c => c.id === mem.category)?.icon} {mem.category}</span>
                      <span className="importance-badge">Importance: {mem.importance}/10</span>
                      <button onClick={() => onDeleteMemory(mem.id)} className="delete-btn">Delete</button>
                    </div>
                    <p className="memory-content">{mem.content}</p>
                    <div className="memory-tags">
                      {mem.tags?.map((tag, j) => <span key={j} className="tag">{tag}</span>)}
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="memory-categories">
                {categories.map(cat => (
                  <div key={cat.id} className="category-section">
                    <h3>{cat.icon} {cat.name}</h3>
                    <button onClick={() => onLoadMemories(cat.id)} className="load-btn">Load</button>
                    <div className="category-memories">
                      {memories.filter(m => m.category === cat.id).map((mem, i) => (
                        <div key={i} className="memory-item small">
                          <p>{mem.content}</p>
                          <button onClick={() => onDeleteMemory(mem.id)}>×</button>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Add Memory Tab */}
        {activeTab === 'add' && (
          <div className="add-memory-tab">
            <h3>Add New Memory</h3>
            <div className="form-group">
              <label>Content</label>
              <textarea
                value={newMemory.content}
                onChange={(e) => setNewMemory({...newMemory, content: e.target.value})}
                placeholder="What do you want to remember?"
                rows={3}
              />
            </div>
            <div className="form-row">
              <div className="form-group">
                <label>Category</label>
                <select
                  value={newMemory.category}
                  onChange={(e) => setNewMemory({...newMemory, category: e.target.value})}
                >
                  {categories.map(cat => (
                    <option key={cat.id} value={cat.id}>{cat.name}</option>
                  ))}
                </select>
              </div>
              <div className="form-group">
                <label>Importance (1-10)</label>
                <input 
                  type="number" 
                  min="1" max="10"
                  value={newMemory.importance}
                  onChange={(e) => setNewMemory({...newMemory, importance: parseInt(e.target.value)})}
                />
              </div>
            </div>
            <div className="form-group">
              <label>Tags (comma separated)</label>
              <input 
                value={newMemory.tags}
                onChange={(e) => setNewMemory({...newMemory, tags: e.target.value})}
                placeholder="tag1, tag2, tag3"
              />
            </div>
            <button onClick={handleAddMemory} className="add-btn">Add Memory</button>
          </div>
        )}

        {/* Conversations Tab */}
        {activeTab === 'conversations' && (
          <div className="conversations-tab">
            <div className="conv-header">
              <h3>Conversation History</h3>
              <div className="conv-actions">
                <button onClick={onLoadConversations} className="load-btn">Refresh</button>
                <button onClick={onClearConversations} className="clear-btn">Clear All</button>
              </div>
            </div>
            <div className="conversations-list">
              {conversations.slice().reverse().map((conv, i) => (
                <div key={i} className={`conversation-item ${conv.role}`}>
                  <span className="conv-role">{conv.role}</span>
                  <p className="conv-content">{conv.content}</p>
                  <span className="conv-time">{conv.timestamp?.split('T')[0] || ''}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Privacy Tab */}
        {activeTab === 'privacy' && (
          <div className="privacy-tab">
            <h3>Privacy Controls</h3>
            <div className="privacy-options">
              <div className="privacy-option">
                <label>
                  <input 
                    type="checkbox"
                    checked={privacySettings?.auto_save !== false}
                    onChange={(e) => onUpdatePrivacy({ auto_save: e.target.checked })}
                  />
                  Auto-save conversations
                </label>
              </div>
              <div className="privacy-option">
                <label>
                  <input 
                    type="checkbox"
                    checked={privacySettings?.encrypt_sensitive !== false}
                    onChange={(e) => onUpdatePrivacy({ encrypt_sensitive: e.target.checked })}
                  />
                  Encrypt sensitive data
                </label>
              </div>
              <div className="privacy-option">
                <label>
                  <input 
                    type="checkbox"
                    checked={privacySettings?.auto_clear_conversations || false}
                    onChange={(e) => onUpdatePrivacy({ auto_clear_conversations: e.target.checked })}
                  />
                  Auto-clear conversations on exit
                </label>
              </div>
            </div>
            <div className="data-management">
              <h4>Data Management</h4>
              <div className="export-import">
                <button onClick={handleExport} className="export-btn">Export Memory</button>
                <div className="import-section">
                  <textarea
                    value={importData}
                    onChange={(e) => setImportData(e.target.value)}
                    placeholder="Paste JSON data to import..."
                    rows={4}
                  />
                  <button onClick={handleImport} className="import-btn">Import</button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Settings Tab */}
        {activeTab === 'settings' && (
          <div className="settings-tab">
            <h3>Memory Settings</h3>
            <div className="settings-section">
              <h4>Clear Data</h4>
              <p> Permanently delete all memories and conversations.</p>
              <div className="danger-zone">
                {categories.map(cat => (
                  <div key={cat.id} className="clear-option">
                    <span>{cat.name}</span>
                    <button onClick={() => onClearCategory(cat.id)} className="clear-btn">Clear</button>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}

export default App;
