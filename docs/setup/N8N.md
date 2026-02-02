# n8n Workflow Automation Setup

Configure n8n for workflow automation and scheduled research tasks.

---

## 📖 Table of Contents

- [Overview](#overview)
- [Initial Setup](#initial-setup)
- [Importing Example Workflow](#importing-example-workflow)
- [Configuring Credentials](#configuring-credentials)
- [Testing Your First Workflow](#testing-your-first-workflow)
- [Understanding the Research Workflow](#understanding-the-research-workflow)
- [Creating Custom Workflows](#creating-custom-workflows)
- [Scheduling Automated Research](#scheduling-automated-research)
- [Common Use Cases](#common-use-cases)
- [Troubleshooting](#troubleshooting)

---

## 📋 Overview

**What is n8n?**  
n8n is a workflow automation tool that connects different services together. In our system, n8n orchestrates the research workflow: triggering document ingestion, running queries, and delivering results.

**Why use n8n?**
- ✅ Schedule automated research (daily ArXiv digest, weekly summaries)
- ✅ Chain multiple operations (ingest → query → email results)
- ✅ Create complex workflows with conditional logic
- ✅ Integrate with external services (email, Slack, webhooks)
- ✅ Visual workflow builder (no coding required)

**Prerequisites**:
- ✅ ResearchAssistantGPT services running
- ✅ n8n accessible at http://localhost:5678

---

## 🚀 Initial Setup

### Step 1: Access n8n

Open your browser and go to:
```
http://localhost:5678
```

### Step 2: Create Admin Account

**First time only**: n8n will prompt you to create an account.

1. **Fill in account details**:
   - **Email**: Your email address (for notifications)
   - **First Name**: Your name
   - **Last Name**: Your surname
   - **Password**: Choose a strong password

2. **Click "Sign Up"**

3. **Accept terms** (if prompted)

4. **Complete setup wizard** (or skip for now)

### Step 3: Understand the Interface

**Main sections**:
- **Workflows**: Left sidebar - List of your workflows
- **Canvas**: Center - Visual workflow editor
- **Node Panel**: Right - Available nodes/actions
- **Executions**: Bottom - Workflow run history

---

## 📥 Importing Example Workflow

We provide a pre-built workflow to get you started.

### Step 1: Locate Example Workflow

The example workflow is in your repository:
```
docker/workflows/research_assistant.json
```

**What it does**:
1. Accepts a research topic (via webhook or manual trigger)
2. Ingests papers from ArXiv
3. Runs research query with multi-agent processing
4. Returns the summary

### Step 2: Import Workflow

**Method 1: Import from File**

1. In n8n, click **"Workflows"** (top left)
2. Click **"Import from File"**
3. Navigate to `docker/workflows/research_assistant.json`
4. Click **"Open"**
5. Workflow appears in canvas

**Method 2: Copy and Paste**

1. Open `docker/workflows/research_assistant.json` in a text editor
2. Copy entire contents (Ctrl+A, Ctrl+C)
3. In n8n, click **"Workflows"** → **"Import from URL or String"**
4. Paste the JSON
5. Click **"Import"**

### Step 3: Save Workflow

1. Click **"Save"** (top right)
2. Give it a name: "Research Assistant - Basic"
3. Click **"Save"**

---

## 🔑 Configuring Credentials

The workflow needs to know how to connect to the API.

### Step 1: Open HTTP Request Node

1. In the workflow canvas, click on any **"HTTP Request"** node
2. The node settings panel opens on the right

### Step 2: Configure API URL

**IMPORTANT**: Use Docker internal network names, not `localhost`!

1. Find the **"URL"** field
2. It should be:
```
   http://api:8000/rag/ingest/arxiv
```
   
   **NOT** `http://localhost:8000`!

**Why?** n8n runs inside Docker and must use internal service names (`api`, not `localhost`).

### Step 3: No Authentication Needed

For local setup, no authentication is required.

1. **Authentication**: Set to **"None"**
2. Click **"Save"** (in node panel)

### Step 4: Repeat for All HTTP Nodes

Go through each HTTP Request node and verify the URLs:

| Node Name | URL |
|-----------|-----|
| **Ingest ArXiv Papers** | `http://api:8000/rag/ingest/arxiv` |
| **Research Query** | `http://api:8000/research/query` |
| **Check API Health** | `http://api:8000/health` |

All should use `http://api:8000`, not `localhost`.

---

## ✅ Testing Your First Workflow

### Step 1: Configure Input

1. Click on the **"Manual Trigger"** node (usually the first node)
2. In the node settings, set test data:
```json
   {
     "topic": "quantum computing",
     "language": "en",
     "max_papers": 3
   }
```

### Step 2: Execute Workflow

1. Click **"Execute Workflow"** (top right)
2. Watch the workflow run:
   - Nodes turn orange while executing
   - Nodes turn green on success
   - Nodes turn red on error

### Step 3: Check Results

1. Click on the **final node** (usually "Research Query")
2. View the output in the right panel
3. You should see:
```json
   {
     "query": "quantum computing",
     "answer": "Quantum computing leverages quantum mechanics principles...",
     "sources": [...],
     "language": "en"
   }
```

**Expected time**: 1-2 minutes for the full workflow.

---

## 🔍 Understanding the Research Workflow

### Workflow Structure
```
Manual Trigger / Webhook
    ↓
HTTP Request: Ingest ArXiv Papers
    ↓
[Wait for ingestion to complete]
    ↓
HTTP Request: Research Query
    ↓
[Process results]
    ↓
Return Response / Send Email
```

### Node Explanations

**1. Manual Trigger**
- **Purpose**: Start workflow manually for testing
- **Alternative**: Use "Webhook" node for external triggers

**2. Set Variables**
- **Purpose**: Define research parameters (topic, language, max papers)
- **Edit**: Double-click to change values

**3. HTTP Request - Ingest ArXiv**
- **URL**: `http://api:8000/rag/ingest/arxiv`
- **Method**: POST
- **Body**: 
```json
  {
    "query": "{{ $json.topic }}",
    "max_results": {{ $json.max_papers }}
  }
```
- **Purpose**: Fetch and ingest papers from ArXiv

**4. Wait Node** (Optional)
- **Purpose**: Pause between ingestion and query
- **Duration**: 5 seconds (ensures embedding is complete)

**5. HTTP Request - Research Query**
- **URL**: `http://api:8000/research/query`
- **Method**: POST
- **Body**:
```json
  {
    "query": "{{ $json.topic }}",
    "language": "{{ $json.language }}"
  }
```
- **Purpose**: Run multi-agent research workflow

**6. Return Response**
- **Purpose**: Show results in n8n UI
- **Alternative**: Replace with "Send Email" node

---

## 🛠️ Creating Custom Workflows

### Example 1: Daily ArXiv Digest

**Goal**: Get daily summaries of new ArXiv papers on a specific topic.

**Nodes**:
1. **Cron**: Trigger daily at 9 AM
   - Expression: `0 9 * * *`
2. **Set Variables**: Define topics
   - `topic`: "machine learning"
   - `max_papers`: 5
3. **HTTP Request**: Ingest papers
4. **HTTP Request**: Research query
5. **Email**: Send results to yourself

**Setup**:

1. Click **"+"** → **"Trigger"** → **"Cron"**
2. Set schedule: `0 9 * * *` (9 AM daily)
3. Add **Set** node:
```json
   {
     "topic": "machine learning",
     "max_papers": 5,
     "language": "en"
   }
```
4. Add **HTTP Request** nodes (same as basic workflow)
5. Add **Send Email** node:
   - To: your.email@example.com
   - Subject: `Daily ArXiv Digest: {{ $json.topic }}`
   - Body: `{{ $json.answer }}`

### Example 2: Webhook-Triggered Research

**Goal**: Trigger research from external applications (Slack, website, etc.)

**Nodes**:
1. **Webhook**: Listen for incoming requests
   - Path: `/research`
   - Method: POST
2. **HTTP Request**: Ingest + Query
3. **Respond to Webhook**: Return results

**Setup**:

1. Add **Webhook** node
2. Set path: `/research`
3. Set method: `POST`
4. **Test URL** will be: `http://localhost:5678/webhook-test/research`
5. **Production URL**: `http://localhost:5678/webhook/research`

**Trigger from external app**:
```powershell
# PowerShell
$body = @{
    topic = "neural networks"
    language = "en"
    max_papers = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:5678/webhook/research" `
    -Method Post `
    -ContentType "application/json" `
    -Body $body
```

### Example 3: Multi-Language Research

**Goal**: Get summaries in multiple languages.

**Nodes**:
1. **Manual Trigger** / **Cron**
2. **Set Variables**: Topic
3. **HTTP Request**: Ingest (once)
4. **Split In Batches**: For each language
   - Languages: `["en", "de", "fr", "es"]`
5. **HTTP Request**: Query (per language)
6. **Aggregate**: Combine results
7. **Email**: Send all translations

---

## ⏰ Scheduling Automated Research

### Cron Expressions

Common schedules:

| Schedule | Cron Expression | Description |
|----------|----------------|-------------|
| Every hour | `0 * * * *` | At minute 0 of every hour |
| Daily at 9 AM | `0 9 * * *` | Every day at 9:00 AM |
| Every Monday 10 AM | `0 10 * * 1` | Monday at 10:00 AM |
| Twice daily | `0 9,18 * * *` | At 9 AM and 6 PM |
| Every 6 hours | `0 */6 * * *` | Every 6 hours |
| Weekdays 8 AM | `0 8 * * 1-5` | Mon-Fri at 8:00 AM |

**Test your cron**: https://crontab.guru/

### Setting Up Scheduled Workflow

1. **Add Cron node**:
   - Click **"+"** → **"Trigger"** → **"Cron"**
   
2. **Configure schedule**:
   - Mode: **"Every Day"** or **"Custom"**
   - Time: Select hour and minute
   - Or enter cron expression

3. **Activate workflow**:
   - Click **"Active"** toggle (top right)
   - Workflow will now run automatically

4. **Monitor executions**:
   - Click **"Executions"** (bottom panel)
   - View past runs and results

---

## 💡 Common Use Cases

### 1. Literature Review Assistant

**Setup**: Weekly summaries of new papers
```
Cron (Weekly: 0 8 * * 1)
    ↓
Set (topic: "computational biology", max: 10)
    ↓
Ingest ArXiv
    ↓
Research Query
    ↓
Format Results
    ↓
Send Email (to research team)
```

### 2. Personal Research Digest

**Setup**: Daily emails with customized topics
```
Cron (Daily: 0 7 * * *)
    ↓
Loop: For each topic in ["AI", "quantum", "neuroscience"]
    ↓
    Ingest ArXiv (per topic)
    ↓
    Research Query (per topic)
    ↓
Aggregate All Results
    ↓
Format as HTML
    ↓
Send Email
```

### 3. On-Demand Research API

**Setup**: Expose research as webhook
```
Webhook (/api/research)
    ↓
Validate Input
    ↓
Ingest ArXiv
    ↓
Research Query
    ↓
Return JSON Response
```

**Usage**:
```powershell
Invoke-RestMethod -Uri "http://localhost:5678/webhook/api/research" `
    -Method Post `
    -Body '{"topic":"deep learning","language":"en"}' `
    -ContentType "application/json"
```

### 4. Slack Integration

**Setup**: Post research summaries to Slack
```
Cron / Manual Trigger
    ↓
Ingest + Query
    ↓
Format for Slack
    ↓
Slack: Send Message
    ↓
Post to #research-updates channel
```

---

## 🔧 Troubleshooting

### Issue: "Connection refused" to API

**Cause**: Using `localhost` instead of `api` service name.

**Solution**:
```
# Wrong
http://localhost:8000/rag/query

# Correct (inside Docker network)
http://api:8000/rag/query
```

### Issue: Workflow times out

**Cause**: Research query takes 25-30 seconds, which may exceed timeout.

**Solution**:
1. Click HTTP Request node
2. Go to **"Options"**
3. Set **"Timeout"**: `60000` (60 seconds)
4. Click **"Save"**

### Issue: n8n can't start (database connection error)

**Cause**: PostgreSQL password mismatch.

**Solution**:
```bash
# Check docker/.env
# Ensure POSTGRES_PASSWORD is set

# Restart services
docker compose restart postgres n8n
```

### Issue: Workflow runs but no results

**Solution**:
1. Check **"Executions"** panel for errors
2. Click on failed execution
3. View error message
4. Common issues:
   - Weaviate not ready → Restart Weaviate
   - No documents in index → Run ingestion first
   - API service down → Check API logs

### Issue: Email not sending

**Solution**:
1. Configure email credentials in n8n:
   - **Credentials** → **"Create New"** → **"SMTP"**
   - Enter your SMTP settings (Gmail, Outlook, etc.)
2. Use credentials in **Send Email** node

---

## 📚 Additional Resources

### n8n Documentation
- **Official Docs**: https://docs.n8n.io/
- **Workflow Templates**: https://n8n.io/workflows/
- **Community Forum**: https://community.n8n.io/

### API Reference
- **Our API Docs**: http://localhost:8000/docs
- **Endpoint Guide**: [docs/api/README.md](../api/README.md)

### Video Tutorials
- **n8n Basics**: https://www.youtube.com/watch?v=RpjQTGKm-ok
- **Creating Workflows**: https://docs.n8n.io/courses/level-one/

---

## ❓ FAQ

**Q: Can I password-protect n8n?**  
A: Yes! Set `N8N_BASIC_AUTH_ACTIVE=true` in `docker/.env` and configure username/password.

**Q: Can I access n8n from other computers on my network?**  
A: Yes! Change `N8N_HOST` in `docker/.env` to your computer's IP address.

**Q: Can I export workflows to share with others?**  
A: Yes! Click workflow → **"Download"** → Saves as JSON file.

**Q: How many workflows can I create?**  
A: Unlimited! n8n has no workflow limits for self-hosted instances.

**Q: Can I integrate with Zapier/Make?**  
A: Yes, via webhooks! n8n can trigger Zapier and vice versa.

---

**[⬅ Back to Setup Guide](README.md)** | **[⬆ Back to Installation](INSTALLATION.md)**