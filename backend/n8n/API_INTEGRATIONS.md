# N8N API Integrations Documentation

## Supported Integrations

### 1. Web Scraping & Data Extraction
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| Bright Data | Scraping | Yes | 🔴 Not Configured |
| ScraperAPI | Scraping | Yes | 🔴 Not Configured |
| Apify | Scraping | Yes | 🔴 Not Configured |

### 2. AI & LLM Providers
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| OpenAI | LLM | Yes | 🔴 Not Configured |
| Anthropic | LLM | Yes | 🔴 Not Configured |
| DeepSeek | LLM | Yes | 🔴 Not Configured |
| NVIDIA | LLM | Yes | 🔴 Not Configured |
| Zhipu AI (GLM) | LLM | Yes | 🔴 Not Configured |
| Ollama | Local | No | 🟡 Local |

### 3. Search & SEO
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| Brave Search | Search | Yes | 🟢 Ready |
| Google Custom Search | Search | Yes | 🔴 Not Configured |
| NightOwl | SEO | Yes | 🔴 Not Configured |

### 4. Social Media
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| Twitter/X | Social | Yes | 🔴 Not Configured |
| LinkedIn | Social | Yes | 🔴 Not Configured |
| Facebook | Social | Yes | 🔴 Not Configured |
| Instagram | Social | Yes | 🔴 Not Configured |

### 5. Email & Marketing
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| Gmail | Email | Yes | 🔴 Not Configured |
| Mailchimp | Marketing | Yes | 🔴 Not Configured |
| SendGrid | Email | Yes | 🔴 Not Configured |
| ConvertKit | Marketing | Yes | 🔴 Not Configured |

### 6. CRM & Sales
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| HubSpot | CRM | Yes | 🔴 Not Configured |
| Salesforce | CRM | Yes | 🔴 Not Configured |
| Pipedrive | CRM | Yes | 🔴 Not Configured |

### 7. Productivity
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| Slack | Chat | Yes | 🔴 Not Configured |
| Discord | Chat | Yes | 🔴 Not Configured |
| Notion | Docs | Yes | 🔴 Not Configured |
| Trello | Project | Yes | 🔴 Not Configured |
| Asana | Project | Yes | 🔴 Not Configured |

### 8. Cloud Storage
| Service | Type | API Key Required | Status |
|---------|------|-----------------|--------|
| Google Drive | Storage | Yes | 🔴 Not Configured |
| Dropbox | Storage | Yes | 🔴 Not Configured |
| AWS S3 | Storage | Yes | 🔴 Not Configured |

---

## API Key Setup Guide

### Step 1: Create API Keys
Copy `.env.example` to `.env` and fill in:
```bash
cp .env.example .env
```

### Step 2: Configure Credentials in N8N
1. Open N8N dashboard
2. Go to Settings → Credentials
3. Add new credentials for each service

### Step 3: Environment Variables
All API keys are loaded from `.env` file automatically.

---

## Webhook Endpoints

| Endpoint | Purpose | Status |
|----------|---------|--------|
| `/webhook/blog-trigger` | Trigger blog generation | 🔴 Not Configured |
| `/webhook/social-post` | Schedule social posts | 🔴 Not Configured |
| `/webhook/lead-capture` | Capture leads | 🔴 Not Configured |
| `/webhook/error-alert` | Error notifications | 🔴 Not Configured |

---

## Rate Limits

| Service | Requests/Hour | Notes |
|---------|---------------|-------|
| OpenAI | 3,000 | Tier 2 |
| Brave Search | 2,000 | Free tier |
| DeepSeek | 500 | Check docs |
| NVIDIA | Varies | Model dependent |

---

## Error Handling

All errors are logged to:
- N8N execution log
- Local file: `logs/n8n-errors.log`
- Slack notification (when configured)
