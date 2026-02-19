# ClawForge v4.0 - API Configuration Guide

## Quick Setup

```bash
cd backend
python setup.py
```

This will check your Python version, dependencies, and API keys.

---

## API Configuration

### 1. NVIDIA API (Recommended - Qwen 3.5 397B)

**Get your free API key:**
- Go to: https://build.nvidia.com/
- Sign up and get your API key

**Add to backend/.env:**
```bash
NVIDIA_API_KEY=nvapi-your-actual-api-key-here
```

**Test:**
```bash
python setup.py
```

### 2. SiliconFlow (OpenAI-compatible Alternative)

**Get your API key:**
- https://siliconflow.cn/

**Add to backend/.env:**
```bash
SILICON_API_KEY=your-siliconflow-key
```

### 3. Ollama (Local - No API Key Needed)

**Install:**
- Download from: https://ollama.com/
- Run: `ollama serve`

**Add to backend/.env:**
```bash
OLLAMA_BASE_URL=http://localhost:11434
```

---

## Starting the Server

### Option 1: Using the launcher (recommended)
```bash
# From the ClawForge root directory
python launcher.py
```

### Option 2: Direct start
```bash
cd backend
python main.py --server
```

### Option 3: Development mode with auto-reload
```bash
cd backend
uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

---

## Accessing ClawForge

- **Dashboard:** http://127.0.0.1:7860
- **API Docs:** http://127.0.0.1:8000/docs
- **Health Check:** http://127.0.0.1:8000/api/health

---

## Troubleshooting

### "Could not connect to the API" Error

This error means the backend server is not running or the API key is missing.

**Solution:**
```bash
# 1. Make sure you're in the ClawForge directory
cd C:\Users\HP\.openclaw\workspace\ClawForge

# 2. Start the server
python backend/main.py --server

# 3. Keep this terminal open
```

### API Key Not Recognized

**Check your .env file:**
```bash
cd backend
cat .env
```

**Make sure it looks like this:**
```bash
NVIDIA_API_KEY=nvapi-actual-key-not-placeholder
```

**Not like this:**
```bash
NVIDIA_API_KEY=nvapi-your-nvidia-api-key-here
```

### Port Already in Use

If port 8000 or 7860 is already in use:

```bash
# Find what's using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /PID PID_NUMBER /F
```

### NVIDIA API Returns 401/403

Your API key might be invalid or expired.

1. Go to https://build.nvidia.com/
2. Check your API key
3. Update backend/.env
4. Restart the server

### Web Search Not Working

Get a Brave Search API key:
- https://brave.com/search/api/

Add to .env:
```bash
BRAVE_API_KEY=your-brave-key
```

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `NVIDIA_API_KEY` | Recommended | For NVIDIA API access |
| `GLM_API_KEY` | No | For GLM-5 (Zhipu AI) |
| `SILICON_API_KEY` | No | For SiliconFlow |
| `OPENROUTER_API_KEY` | No | For OpenRouter |
| `OLLAMA_BASE_URL` | No | For local Ollama |
| `BRAVE_API_KEY` | No | For web search |

---

## Production Deployment

### Using Docker
```bash
docker build -t clawforge .
docker run -p 8000:8000 -p 7860:7860 clawforge
```

### Using Gunicorn
```bash
cd backend
gunicorn api:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## Getting Help

1. **Check the logs:** Backend console output
2. **API health:** http://127.0.0.1:8000/api/status
3. **Documentation:** README.md in backend folder
