# N8N Workflow Automation Setup

## Quick Start

### Option 1: Docker (Recommended)
```bash
cd backend/n8n
cp .env.example .env
# Edit .env with your credentials
docker-compose up -d
```

Access N8N at: http://localhost:5678

### Option 2: npm
```bash
cd backend/n8n
npm install n8n -g
n8n start
```

---

## Directory Structure

```
n8n/
├── docker-compose.yml    # Docker configuration
├── .env.example         # Environment template
├── .env                 # Your actual credentials (gitignored)
├── API_INTEGRATIONS.md  # API setup guide
├── error_handler.py     # Error handling system
├── monitor.py           # Health monitoring
├── workflows/           # Importable workflows
│   ├── content-distribution.json
│   ├── lead-capture.json
│   └── email-automation.json
└── shared/              # Shared resources
```

---

## Initial Setup Checklist

- [ ] Copy `.env.example` to `.env`
- [ ] Add N8N password in `.env`
- [ ] Configure API credentials in N8N dashboard
- [ ] Import workflows from `workflows/` folder
- [ ] Activate workflows
- [ ] Test error handler: `python error_handler.py`
- [ ] Start monitor: `python monitor.py --continuous`

---

## Default Credentials

- **Username:** admin
- **Password:** (set in `.env` file)

---

## Available Workflows

| Workflow | Purpose | Triggers |
|----------|---------|----------|
| Content Distribution | Auto-share blog posts to social | New file in Google Drive |
| Lead Capture | Capture and route leads | Webhook |
| Email Automation | Drip email campaigns | Scheduled |
| Error Alerting | Send errors to Slack | Error occurrence |

---

## Monitoring

### Health Check
```bash
python monitor.py --url http://localhost:5678
```

### Continuous Monitoring
```bash
python monitor.py --url http://localhost:5678 --continuous
```

---

## Next Steps

1. **Add more API credentials** in N8N dashboard
2. **Import additional workflows** from templates
3. **Configure webhooks** for external triggers
4. **Set up Slack notifications** for errors
