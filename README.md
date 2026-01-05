# HACI Quick Start

> **Get HACI running in 15 minutes** and see AI-powered support automation in action

<div align="center">

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## What You'll Experience

In this quick start, you'll:

1. ✅ Launch a minimal HACI environment
2. ✅ Submit your first automated investigation
3. ✅ See the **THINK→ACT→OBSERVE→EVALUATE** harness pattern in action
4. ✅ Experience confidence-based human approval workflows

**Time:** 15 minutes  
**Prerequisites:** Docker OR Python 3.11+, plus an API key (Anthropic recommended)

---

## Option A: Docker Quick Start (5 minutes)

The fastest way to see HACI in action.

### Step 1: Clone and Configure

```bash
git clone https://github.com/shawnbray205/HACI-quickstart.git
cd haci-quickstart

cp .env.example .env
```

### Step 2: Add Your API Key

Edit `.env`:

```bash
# Anthropic recommended
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Or use OpenAI
# OPENAI_API_KEY=sk-your-key-here
```

### Step 3: Launch

```bash
docker-compose up -d
```

### Step 4: Open the Demo

Navigate to: **http://localhost:8080**

Click **"Submit Test Ticket"** and watch the investigation unfold in real-time!

---

## Option B: Python Quick Start (15 minutes)

For developers who want to understand the code.

### Step 1: Setup

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### Step 2: Configure

```bash
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
```

### Step 3: Run the Demo

```bash
python haci_demo.py
```

You'll see a simulated investigation with the harness pattern:

```
🎯 Submitting ticket: API returning 502 errors intermittently
============================================================
🧠 THINK: Forming hypothesis...
⚡ ACT: Querying Datadog for recent 502 errors...
👁️ OBSERVE: Found 47 502 errors in last hour, spike at 14:23 UTC
🧠 THINK: Correlating with deployment timeline...
⚡ ACT: Checking GitHub deployments...
👁️ OBSERVE: Deployment at 14:20 UTC - config change to connection pool
✅ EVALUATE: Root cause identified with 94% confidence

📋 RESOLUTION:
   Root Cause: Connection pool misconfiguration in deployment abc123
   Recommended Fix: Rollback deployment or increase pool_size to 50
   Confidence: 94%
   Action: AUTO-EXECUTE (above 95% threshold for review)
```

---

## What's Happening Under the Hood

The demo implements HACI's core **harness pattern**:

```
┌─────────────────────────────────────────────────────────┐
│                    HARNESS LOOP                         │
│                                                         │
│   ┌──────────┐     ┌─────────┐     ┌──────────────┐    │
│   │  THINK   │────▶│   ACT   │────▶│   OBSERVE    │    │
│   │          │     │         │     │              │    │
│   │ Hypothesize    │ Execute │     │ Analyze      │    │
│   │ Plan next │    │ tools   │     │ results      │    │
│   └──────────┘     └─────────┘     └──────────────┘    │
│         ▲                                │              │
│         │          ┌──────────┐          │              │
│         └──────────│ EVALUATE │◀─────────┘              │
│                    │          │                         │
│                    │ Confidence│                        │
│                    │ Gate      │                        │
│                    └──────────┘                         │
└─────────────────────────────────────────────────────────┘
```

### Confidence-Based Action Gating

| Confidence | Action |
|------------|--------|
| ≥ 95% | Auto-execute |
| 85-94% | Execute with review |
| 70-84% | Require approval |
| < 70% | Human-led |

---

## Next Steps

Ready for the full HACI experience?

| Resource | Description |
|----------|-------------|
| [Full Repository](https://github.com/shawnbray205/HACI) | Complete HACI implementation |
| [Documentation](https://docs.haci.ai) | Comprehensive guides |
| [LangSmith Guide](./docs/langsmith-guide.md) | Observability setup |

---

## Troubleshooting

### "No module named 'langgraph'"

```bash
pip install langgraph langchain-anthropic
```

### "Invalid API key"

```bash
echo $ANTHROPIC_API_KEY  # Verify it's set
```

### Docker won't start

```bash
docker-compose down -v
docker-compose up -d
docker-compose logs
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**You're 15 minutes away from AI-powered automation!** 🚀

</div>
