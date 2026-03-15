# ReefSync — Person 3: AI Layer

## What's in here

```
backend/
├── ai/
│   ├── __init__.py
│   ├── client.py        # Anthropic SDK wrapper (call_claude, streaming, JSON, multi-turn)
│   └── prompts.py       # All system prompts as versioned constants
├── routers/
│   └── ai_routes.py     # All /ai/* FastAPI endpoints
└── test_ai.py           # Smoke test — run after server is up
```

## Setup

```bash
pip install anthropic fastapi
export ANTHROPIC_API_KEY=sk-ant-...
```

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/ai/site-summary` | Plain-English summary for a reef site |
| POST | `/ai/site-summary/stream` | Same, but Server-Sent Events streaming |
| POST | `/ai/recommend-sites` | Top 3 survey picks for a diver |
| POST | `/ai/gap-report` | Markdown gap report for org admins |
| POST | `/ai/follow-up` | Multi-turn Q&A about a specific site |

## How Person 2 mounts this router

In `backend/main.py`, Person 2 adds **one line**:

```python
from routers.ai_routes import router as ai_router
app.include_router(ai_router)
```

That's it — no other changes needed to existing code.

## How Person 4 uses the streaming endpoint (frontend)

```javascript
const response = await fetch('/ai/site-summary/stream', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(siteData),
});
const reader = response.body.getReader();
const decoder = new TextDecoder();
let summaryText = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;
  const lines = decoder.decode(value).split('\n');
  for (const line of lines) {
    if (line.startsWith('data: ') && line !== 'data: [DONE]') {
      const parsed = JSON.parse(line.slice(6));
      if (parsed.chunk) {
        summaryText += parsed.chunk;
        document.getElementById('ai-summary').textContent = summaryText;
      }
    }
  }
}
```

## Tuning prompts

Edit `ai/prompts.py` only. Add a version comment when you change a prompt:

```python
# v1.1 - Added urgency scoring to site summary
SITE_SUMMARY_SYSTEM = """..."""
```

## Running smoke tests

With the FastAPI server running (`uvicorn main:app --reload`):

```bash
python test_ai.py
```
