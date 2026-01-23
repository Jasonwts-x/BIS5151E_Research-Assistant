# n8n Workflow Examples

Example workflows for automating research tasks with n8n.

## Table of Contents

1. [Setup](#setup)
2. [Basic Workflows](#basic-workflows)
3. [Advanced Workflows](#advanced-workflows)
4. [Scheduled Workflows](#scheduled-workflows)
5. [Integration Examples](#integration-examples)

---

## Setup

### 1. Access n8n UI

Open http://localhost:5678 in your browser.

### 2. Create Credentials

**HTTP Credential**:
1. Click **Credentials** → **New**
2. Select **HTTP Request**
3. Configure:
   - Name: `Research Assistant API`
   - Authentication: `None` (local development)
   - Base URL: `http://api:8000`

### 3. Test Connection

Create a simple workflow:
1. Add **HTTP Request** node
2. URL: `{{$credentials.baseUrl}}/health`
3. Method: `GET`
4. Execute

Expected: `{"status": "ok"}`

---

## Basic Workflows

### Workflow 1: Daily Paper Summary

**Description**: Fetch latest papers and send summary via email

**Nodes**:
```
1. Schedule Trigger (Daily 9am)
   ↓
2. HTTP: Ingest ArXiv
   ↓
3. Wait (2 min for ingestion)
   ↓
4. HTTP: Query Summary
   ↓
5. Send Email
```

**Configuration**:

**Node 1 - Schedule Trigger**:
```json
{
  "rule": "0 9 * * *",
  "timezone": "Europe/Berlin"
}
```

**Node 2 - Ingest ArXiv**:
```json
{
  "method": "POST",
  "url": "http://api:8000/rag/ingest/arxiv",
  "body": {
    "query": "large language models",
    "max_results": 5
  }
}
```

**Node 3 - Wait**:
```json
{
  "amount": 2,
  "unit": "minutes"
}
```

**Node 4 - Query**:
```json
{
  "method": "POST",
  "url": "http://api:8000/rag/query",
  "body": {
    "query": "Summarize recent advances in large language models",
    "language": "en"
  }
}
```

**Node 5 - Email**:
```json
{
  "to": "researcher@example.com",
  "subject": "Daily AI Research Summary - {{$today}}",
  "text": "{{$json.answer}}"
}
```

---

### Workflow 2: On-Demand Research

**Description**: Trigger research via webhook

**Nodes**:
```
1. Webhook Trigger
   ↓
2. HTTP: Query
   ↓
3. Webhook Response
```

**Configuration**:

**Node 1 - Webhook**:
- Method: POST
- Path: `research`
- URL: `http://localhost:5678/webhook/research`

**Node 2 - Query**:
```json
{
  "method": "POST",
  "url": "http://api:8000/rag/query",
  "body": {
    "query": "{{$json.body.topic}}",
    "language": "{{$json.body.language || 'en'}}"
  }
}
```

**Node 3 - Response**:
```json
{
  "response": "{{$node['HTTP Request'].json}}"
}
```

**Usage**:
```bash
curl -X POST http://localhost:5678/webhook/research \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "What is RAG?",
    "language": "en"
  }'
```

---

### Workflow 3: Multi-Topic Summary

**Description**: Research multiple topics and combine summaries

**Nodes**:
```
1. Manual Trigger
   ↓
2. Set Topics (Code node)
   ↓
3. Split In Batches
   ↓
4. HTTP: Query (per topic)
   ↓
5. Aggregate Results
   ↓
6. Save to File
```

**Node 2 - Set Topics**:
```javascript
const topics = [
  "transformers architecture",
  "attention mechanisms",
  "retrieval augmented generation"
];

return topics.map(topic => ({json: {topic}}));
```

**Node 4 - Query**:
```json
{
  "method": "POST",
  "url": "http://api:8000/rag/query",
  "body": {
    "query": "{{$json.topic}}",
    "language": "en"
  }
}
```

**Node 5 - Aggregate**:
```javascript
const summaries = $items().map(item => ({
  topic: item.json.query,
  answer: item.json.answer
}));

const combined = summaries.map(s => 
  `## ${s.topic}\n\n${s.answer}`
).join('\n\n---\n\n');

return [{json: {combined}}];
```

---

## Advanced Workflows

### Workflow 4: Conditional Ingestion

**Description**: Check index size, ingest only if below threshold

**Nodes**:
```
1. Schedule Trigger
   ↓
2. HTTP: Get Stats
   ↓
3. IF: Document count < 100
   ├─ True → Ingest ArXiv
   └─ False → Skip
   ↓
4. Send Status Email
```

**Node 3 - Condition**:
```json
{
  "conditions": {
    "number": [
      {
        "value1": "={{$json.document_count}}",
        "operation": "smaller",
        "value2": 100
      }
    ]
  }
}
```

---

### Workflow 5: Quality Check

**Description**: Validate summary quality before sending

**Nodes**:
```
1. Webhook Trigger
   ↓
2. HTTP: Query
   ↓
3. Code: Check Quality
   ↓
4. IF: Quality OK
   ├─ True → Send Email
   └─ False → Log Error
```

**Node 3 - Quality Check**:
```javascript
const answer = $json.answer;

// Quality checks
const hasMinLength = answer.length > 200;
const hasCitations = /\[\d+\]/.test(answer);
const hasContent = !answer.includes("No context available");

const qualityOK = hasMinLength && hasCitations && hasContent;

return [{
  json: {
    ...item.json,
    quality: {
      ok: qualityOK,
      checks: {hasMinLength, hasCitations, hasContent}
    }
  }
}];
```

---

## Scheduled Workflows

### Weekly Digest

**Schedule**: Every Monday 9am

**Workflow**:
```
1. Schedule: Cron (0 9 * * 1)
   ↓
2. Ingest: Last week's papers
   ↓
3. Query: Weekly summary
   ↓
4. Format: Markdown
   ↓
5. Email: Weekly digest
```

**Ingest Query** (last 7 days):
```json
{
  "query": "submittedDate:[NOW-7DAYS TO NOW]",
  "max_results": 20
}
```

---

### Monthly Report

**Schedule**: First day of month

**Workflow**:
```
1. Schedule: Cron (0 9 1 * *)
   ↓
2. Multiple Queries (topics)
   ↓
3. Generate Report
   ↓
4. Save to Google Drive
   ↓
5. Notify Team (Slack)
```

---

## Integration Examples

### Slack Integration

**Send summaries to Slack**:

**Nodes**:
```
1. Schedule/Webhook
   ↓
2. Query API
   ↓
3. Slack: Post Message
```

**Slack Node**:
```json
{
  "channel": "#research-updates",
  "text": "*Daily Research Summary*\n\n{{$json.answer}}"
}
```

---

### Google Drive Integration

**Save summaries to Drive**:

**Nodes**:
```
1. Query API
   ↓
2. Google Drive: Create File
```

**Drive Node**:
```json
{
  "name": "Summary_{{$today}}.txt",
  "content": "{{$json.answer}}",
  "parents": ["folder_id"]
}
```

---

### Notion Integration

**Create Notion page with summary**:

**Nodes**:
```
1. Query API
   ↓
2. Notion: Create Page
```

**Notion Node**:
```json
{
  "database": "Research Database",
  "title": "{{$json.query}}",
  "properties": {
    "Summary": "{{$json.answer}}",
    "Date": "{{$today}}",
    "Status": "Completed"
  }
}
```

---

## Error Handling

### Retry Logic
```
1. Query API
   ↓
2. IF: Error
   ├─ True → Wait 30s → Retry (max 3x)
   └─ False → Continue
```

**Error Check**:
```javascript
const hasError = $json.error !== undefined;
const retryCount = $env.RETRY_COUNT || 0;

if (hasError && retryCount < 3) {
  $env.RETRY_COUNT = retryCount + 1;
  return {error: true, retry: true};
}

return {error: hasError, retry: false};
```

---

### Fallback Workflow
```
1. Try: Primary API
   ↓
2. IF: Failed
   └─ Fallback: Secondary source
   ↓
3. Continue
```

---

## Best Practices

### 1. Always Check Service Health

Add health check before expensive operations:
```
1. HTTP: GET /ready
   ↓
2. IF: status == "ok"
   └─ Continue
   └─ Alert & Exit
```

### 2. Use Wait Nodes for Ingestion

Ingestion is async:
```
1. Ingest
   ↓
2. Wait 1-2 minutes
   ↓
3. Query
```

### 3. Log Workflow Execution

Add logging nodes:
```javascript
console.log('Workflow step completed', {
  step: 'ingestion',
  timestamp: new Date().toISOString(),
  result: $json
});
```

### 4. Handle Rate Limits

Add delays between requests:
```
1. Loop Items
   ↓
2. Process Item
   ↓
3. Wait 1s
   ↓
4. Next Item
```

---

## Sample Workflows (Import Ready)

### Simple Query Workflow (JSON)
```json
{
  "name": "Simple Research Query",
  "nodes": [
    {
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "parameters": {
        "path": "research"
      }
    },
    {
      "name": "Query API",
      "type": "n8n-nodes-base.httpRequest",
      "parameters": {
        "url": "http://api:8000/rag/query",
        "method": "POST",
        "bodyParameters": {
          "query": "={{$json.body.topic}}",
          "language": "en"
        }
      }
    },
    {
      "name": "Respond",
      "type": "n8n-nodes-base.respondToWebhook",
      "parameters": {
        "response": "={{$json}}"
      }
    }
  ]
}
```

**Import**: Copy to n8n → Settings → Import from JSON

---

## Troubleshooting

### Common Issues

**1. "Connection Refused"**
- Check API is running: `docker compose ps api`
- Use internal Docker network URL: `http://api:8000`

**2. "Timeout"**
- Increase timeout in HTTP Request node (60-120s)
- Add Wait node after ingestion

**3. "Empty Response"**
- Check index has documents: GET /rag/stats
- Ingest documents first

---

**[⬆ Back to Examples](README.md)**