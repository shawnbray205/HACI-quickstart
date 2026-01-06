# HACI Quick Start

> **Experience AI-powered incident investigation in 5 minutes**

<div align="center">

[![Docker](https://img.shields.io/badge/docker-ready-blue.svg)](https://www.docker.com/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**[Live Demo](#quick-start) • [Full Documentation](https://github.com/shawnbray205/HACI) • [How It Works](#how-it-works)**

</div>

---

## What This Demo Shows

This quick start demonstrates HACI's core **Harness Pattern** - the THINK→ACT→OBSERVE→EVALUATE loop that powers intelligent incident investigation:

| Phase | What Happens | You'll See |
|-------|--------------|------------|
| 🧠 **THINK** | LLM forms hypotheses about root cause | Hypothesis generation with confidence scores |
| ⚡ **ACT** | Execute monitoring tools (Datadog, GitHub, etc.) | Real tool calls with parameters and results |
| 👁️ **OBSERVE** | LLM analyzes evidence | Pattern detection and correlation |
| ✅ **EVALUATE** | Assess confidence and decide action | Confidence-based action gating |

**Key Feature: Confidence-Based Action Gating**

```
≥95% → 🟢 Auto-Execute (no human needed)
85-94% → 🟡 Execute with Review notification  
70-84% → 🟠 Require Human Approval
<70% → 🔴 Continue Investigation or Escalate
```

---

## Quick Start

### Option A: Web Demo (Recommended)

```bash
# Clone and setup
git clone https://github.com/shawnbray205/HACI-quickstart.git
cd HACI-quickstart

# Install dependencies
pip install -r requirements.txt

# Set your API key (Anthropic recommended)
export ANTHROPIC_API_KEY="sk-ant-your-key-here"
# OR: export OPENAI_API_KEY="sk-your-key-here"

# Launch the web demo
python web_demo.py
```

Open **http://localhost:8080** and click "Start Investigation"

You'll see:
- Real-time harness loop visualization
- LLM reasoning displayed as it happens
- Tool execution with actual parameters
- Confidence meter with threshold indicators
- Final resolution with actionable command

### Option B: Terminal Demo

```bash
# Same setup as above, then:
python haci_demo.py
```

This shows a detailed terminal output with:
- Color-coded phases
- LLM prompts and responses
- Tool execution details
- Confidence assessment
- Production behavior explanation

---

## What You'll Experience

### 1. Hypothesis Formation (THINK)
```
🧠 THINK - Forming Hypotheses
────────────────────────────────────────────────────────────

  🤖 LLM Call (ANTHROPIC):
  ┌─ Phase: THINK
  ├─ Prompt: "Investigate this ticket..."
  ├─ Reasoning:
  │    The timing of errors starting at 14:21 suggests a recent
  │    change triggered this issue. Need to correlate with deployment.
  └─ Response keys: ['hypotheses', 'next_actions', 'reasoning']

  📊 Hypotheses Generated:
     1. Recent deployment changed connection pool configuration
        Confidence: [███████░░░] 75%
        Evidence needed: deployment logs, config changes
```

### 2. Tool Execution (ACT)
```
⚡ ACT - Gathering Evidence
────────────────────────────────────────────────────────────

  🔧 Tool: datadog_logs_search
     ├─ Description: Search application logs in Datadog
     ├─ Parameters: {"query": "service:api-gateway status:error"}
     └─ Result: Found 47 log entries | 47 errors | Error rate: 23.5%

  🔧 Tool: github_deployments  
     ├─ Description: Get recent deployments from GitHub
     ├─ Parameters: {"repo": "main-service", "limit": 5}
     └─ Result: Found deployment abc123 at 2024-01-15T14:20:00Z
```

### 3. Evidence Analysis (OBSERVE)
```
👁️ OBSERVE - Analyzing Evidence
────────────────────────────────────────────────────────────

  🔍 Findings Extracted:
     🔴 [CRITICAL] Deployment abc123 reduced connection pool from 10 to 5
        Confidence: 98%

     🔴 [CRITICAL] Database connections at 100% capacity (5/5 active)
        Confidence: 96%

  🔗 Correlations Identified:
     • Deployment abc123 (14:20) → Pool exhaustion (14:21) → 502 errors
```

### 4. Confidence Assessment (EVALUATE)
```
✅ EVALUATE - Confidence Assessment
────────────────────────────────────────────────────────────

  📊 Confidence Score:
     [████████████████████████████████████████] 94%

     Confidence Thresholds:
       ○ 95% - Auto Execute
       ✓ 85% - Execute With Review
       ✓ 70% - Require Approval

  ⚡ Action Decision:
     🟡 EXECUTE WITH REVIEW
     Confidence 85-94% - executing with post-action review notification

  🎯 Root Cause:
     Connection pool misconfiguration in deployment abc123 reduced
     pool_size from 10 to 5, causing immediate exhaustion under normal load

  💡 Recommended Resolution:
     Action: Rollback deployment abc123 to restore pool_size=10
     $ kubectl rollout undo deployment/api-gateway --to-revision=previous
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────────┐
│                      HACI HARNESS                           │
│                                                             │
│   ┌──────────┐    ┌─────────┐    ┌──────────┐              │
│   │  THINK   │───▶│   ACT   │───▶│ OBSERVE  │              │
│   │          │    │         │    │          │              │
│   │ LLM forms│    │ Execute │    │ LLM      │              │
│   │ hypotheses    │ tools   │    │ analyzes │              │
│   └──────────┘    └─────────┘    └──────────┘              │
│         ▲                              │                    │
│         │         ┌──────────┐         │                    │
│         └─────────│ EVALUATE │◀────────┘                    │
│                   │          │                              │
│                   │ Confidence                              │
│                   │ Gate     │                              │
│                   └──────────┘                              │
│                        │                                    │
│         ┌──────────────┼──────────────┐                    │
│         ▼              ▼              ▼                    │
│    ┌─────────┐   ┌──────────┐   ┌─────────┐               │
│    │  <70%   │   │  70-94%  │   │  ≥95%   │               │
│    │Continue │   │  Human   │   │  Auto   │               │
│    │  Loop   │   │ Approval │   │ Execute │               │
│    └─────────┘   └──────────┘   └─────────┘               │
└─────────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# LLM Provider (choose one)
ANTHROPIC_API_KEY=sk-ant-...    # Recommended
OPENAI_API_KEY=sk-...            # Alternative

# Demo settings
DEMO_PORT=8080                   # Web demo port
```

### Confidence Thresholds

Edit in `haci_demo.py`:

```python
CONFIDENCE_THRESHOLDS = {
    "auto_execute": 95,      # No human needed
    "execute_review": 85,    # Execute + notify
    "require_approval": 70,  # Wait for approval
}
```

---

## Demo vs Production

| Feature | This Demo | Full HACI |
|---------|-----------|-----------|
| Agents | 1 (meta-orchestrator) | 10 specialized agents |
| Tools | 4 mock integrations | 50+ real integrations |
| LLM | Claude/GPT-4 | Multi-provider routing |
| Approval | Simulated | Slack/Email/PagerDuty |
| Persistence | In-memory | PostgreSQL + Redis |
| Observability | Console logs | LangSmith + Grafana |

---

## Next Steps

Ready for the full HACI experience?

1. **[Full Repository](https://github.com/shawnbray205/HACI)** - Complete implementation with 10 agents
2. **[Technical Documentation](https://github.com/shawnbray205/HACI/docs)** - Architecture deep-dive
3. **[Integration Guide](https://github.com/shawnbray205/HACI/docs/integration)** - Connect your tools

---

## Troubleshooting

### No API key
```
⚠ Demo Mode (No API Key)
```
The demo works without an API key using realistic mock responses. Add a key to see real LLM reasoning.

### Module not found
```bash
pip install anthropic fastapi uvicorn pydantic
```

### Port in use
```bash
DEMO_PORT=3000 python web_demo.py
```

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

<div align="center">

**Built with ❤️ for the future of AI-powered operations**

[⭐ Star on GitHub](https://github.com/shawnbray205/HACI) • [📖 Documentation](https://github.com/shawnbray205/HACI) • [🐛 Report Bug](https://github.com/shawnbray205/HACI/issues)

</div>
