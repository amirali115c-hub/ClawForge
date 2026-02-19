# ClawForge v4.0 - Quick Start Guide

## 🚀 Launch on Your Machine

### 1. Pull Ollama model
```bash
ollama pull llama3
```

### 2. Start everything

**Linux/Mac:**
```bash
bash start_all.sh
```

**Windows (Terminal 1):**
```powershell
.\start_backend.ps1
```

**Windows (Terminal 2):**
```powershell
.\start_frontend.ps1
```

### 3. Open dashboard
```
http://127.0.0.1:7860
```

---

## 💻 Or use CLI directly

```bash
# Run a task
python backend/main.py --task "Write an SEO blog about AI tools"

# Generate a project
python backend/main.py --generate "Build a FastAPI with auth"

# Run demo
python backend/main.py --demo
```

---

## 📦 Dependencies

```bash
pip install -r requirements.txt
```
