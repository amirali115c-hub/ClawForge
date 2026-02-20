# Leo 2.0 - Production-Grade Autonomous AI Agent Framework

<p align="center">
  <img src="https://img.shields.io/badge/version-2.0.0-blue" alt="Version">
  <img src="https://img.shields.io/badge/Python-3.8+-green" alt="Python">
  <img src="https://img.shields.io/badge/license-MIT-yellow" alt="License">
</p>

A production-grade autonomous AI agent framework for building, deploying, and managing AI-powered automation systems.

## 🎯 What is Leo 2.0?

Leo 2.0 is NOT a chatbot. It's a full-stack AI operator that can:

- 📝 **Write Content** - Blog posts, articles, social media
- 💻 **Build Software** - Code generation, debugging, full-stack apps
- 🔄 **Automate Tasks** - Workflows, scheduling, integrations
- 🧠 **Plan & Execute** - Multi-step task planning
- 🔧 **Use Tools** - Safe tool execution with permission gating

## ⚡ Quick Start

### Option 1: Double-Click (Windows)
```
Double-click START_CLAWFORGE.bat
```

### Option 2: Setup + Start
```bash
# Check configuration
python backend/setup.py

# Start the server
python backend/main.py --server
```

### Option 3: Docker
```bash
docker-compose up -d
```

---

## 🖥️ Access Points

| Service | URL | Description |
|---------|-----|-------------|
| Dashboard | http://127.0.0.1:7860 | React web interface |
| API | http://127.0.0.1:8000 | REST API |
| API Docs | http://127.0.0.1:8000/docs | Swagger documentation |
| Health | http://127.0.0.1:8000/api/health | Health check |

---

## 🔑 API Configuration

### NVIDIA API (Recommended)

1. Get your free API key: https://build.nvidia.com/
2. Add to `backend/.env`:
```bash
NVIDIA_API_KEY=nvapi-your-key-here
```

### Other Providers

| Provider | Setup |
|----------|-------|
| SiliconFlow | Add `SILICON_API_KEY` to .env |
| Ollama (Local) | Install from ollama.com, set `OLLAMA_BASE_URL` |
| GLM-5 | Add `GLM_API_KEY` to .env |

See [backend/API_CONFIGURATION.md](backend/API_CONFIGURATION.md) for detailed setup.

---

## ✨ Features

### Core Capabilities
- 🤖 **4 AI Models** - NVIDIA, SiliconFlow, Ollama, GLM-5
- 🧠 **Task Planning** - Multi-step execution with approval gates
- 🔧 **Tool Execution** - 20+ safe tools with permission system
- 💾 **Memory** - Long-term and short-term memory
- 🔒 **Security** - 5-layer security with risk scoring

### Tools Available
| Category | Tools |
|----------|-------|
| Files | read_file, write_file, create_folder, delete_file |
| Terminal | run_command, list_processes |
| Code | run_python, lint_code, create_project |
| Browser | open_url, extract_content |
| Office | create_docx, create_pdf, create_spreadsheet |
| UI Automation | take_screenshot, click, type_text |

### Security Layers
1. **Task Risk Analyzer** - Blocks dangerous patterns
2. **Data Exfiltration Prevention** - Blocks workspace escape
3. **Prompt Injection Protector** - Detects jailbreak attempts
4. **Permission System** - User approval for risky actions
5. **Kill Switch** - Emergency stop for all operations

---

## 📁 Project Structure

```
Leo 2.0/
├── backend/
│   ├── api.py              # FastAPI server
│   ├── config.py           # Configuration management
│   ├── setup.py            # Setup & diagnostic tool
│   ├── api.py              # Main API endpoints
│   ├── features.py         # Feature implementations
│   ├── tools.py           # Tool router & executors
│   ├── task_manager.py    # Task lifecycle
│   ├── planner.py         # Task planning
│   ├── security.py         # Security layers
│   ├── memory.py          # Memory management
│   ├── nvidia_client.py   # NVIDIA API
│   ├── ollama_client.py   # Ollama local
│   └── .env.example       # Environment template
├── frontend/
│   └── src/
│       └── App.jsx        # React dashboard
├── context/                # Context integration
├── workflows/             # N8N workflows
└── launcher.py            # Service launcher
```

---

## 🚀 Deployment

### Local Development
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start backend
python backend/main.py --server

# Start frontend (separate terminal)
cd frontend && npm install && npm run dev
```

### Production
```bash
# Using Docker
docker-compose up -d

# Or using gunicorn
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 📝 Usage

### Using the Dashboard
1. Open http://127.0.0.1:7860
2. Create a task or use the chat interface
3. Approve any permission requests
4. Watch the agent work

### Using the API
```bash
# Create a task
curl -X POST http://127.0.0.1:8000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"goal": "Write a Python script", "category": "code_generation"}'

# Chat with AI
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Help me write a blog post about AI"}'
```

---

## 🔧 Configuration

### Environment Variables

```bash
# API Keys
NVIDIA_API_KEY=nvapi-your-key
GLM_API_KEY=
SILICON_API_KEY=

# Server
LEO_HOST=127.0.0.1
LEO_PORT=8000
LEO_FRONTEND_PORT=7860
```

### Security Modes

| Mode | Description |
|------|-------------|
| `LOCKED` | Maximum security, requires approval for most actions |
| `SAFE` | Balanced security, auto-approve low-risk actions |
| `DEVELOPER` | Full access, for development only |

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

---

**Built with ❤️ for autonomous AI agents**
**Created by Amir Ali (Project Shahzada)**
