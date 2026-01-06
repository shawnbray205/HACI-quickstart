"""
HACI Enhanced Web Demo
======================
Interactive web interface showing the HACI harness pattern with real-time streaming.
"""

import asyncio
import json
import os
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn

app = FastAPI(title="HACI Demo")

# Import the demo components
from haci_demo import (
    HACIHarness, HarnessState, CONFIDENCE_THRESHOLDS,
    MOCK_DATA, LLMClient
)


# =============================================================================
# ENHANCED HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HACI - AI Investigation Demo</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg-primary: #0a0a0f;
            --bg-secondary: #12121a;
            --bg-card: #1a1a24;
            --bg-hover: #22222e;
            --text-primary: #ffffff;
            --text-secondary: #a0a0b0;
            --text-dim: #606070;
            --accent-blue: #3b82f6;
            --accent-cyan: #06b6d4;
            --accent-green: #10b981;
            --accent-yellow: #f59e0b;
            --accent-red: #ef4444;
            --accent-purple: #8b5cf6;
            --border: #2a2a3a;
        }
        
        * { box-sizing: border-box; margin: 0; padding: 0; }
        
        body {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
            background: var(--bg-primary);
            color: var(--text-primary);
            min-height: 100vh;
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        /* Header */
        header {
            text-align: center;
            padding: 40px 20px;
            background: linear-gradient(180deg, var(--bg-secondary) 0%, transparent 100%);
            border-bottom: 1px solid var(--border);
            margin-bottom: 30px;
        }
        
        .logo {
            font-size: 2.5rem;
            font-weight: 700;
            background: linear-gradient(135deg, var(--accent-cyan), var(--accent-blue));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 10px;
        }
        
        .tagline {
            color: var(--text-secondary);
            font-size: 1.1rem;
        }
        
        .provider-badge {
            display: inline-block;
            margin-top: 15px;
            padding: 6px 14px;
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 0.85rem;
            color: var(--accent-green);
        }
        
        /* Cards */
        .card {
            background: var(--bg-card);
            border: 1px solid var(--border);
            border-radius: 12px;
            padding: 24px;
            margin-bottom: 20px;
        }
        
        .card-title {
            font-size: 1rem;
            font-weight: 600;
            color: var(--text-secondary);
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        /* Ticket Input */
        .ticket-input {
            width: 100%;
            padding: 16px;
            background: var(--bg-primary);
            border: 1px solid var(--border);
            border-radius: 8px;
            color: var(--text-primary);
            font-size: 1rem;
            font-family: inherit;
            margin-bottom: 16px;
            transition: border-color 0.2s;
        }
        
        .ticket-input:focus {
            outline: none;
            border-color: var(--accent-blue);
        }
        
        .btn {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            padding: 12px 24px;
            background: linear-gradient(135deg, var(--accent-blue), var(--accent-cyan));
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(59, 130, 246, 0.3);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
        }
        
        /* Harness Visualization */
        .harness-container {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 20px 0;
            gap: 10px;
        }
        
        .harness-step {
            flex: 1;
            text-align: center;
            padding: 20px 10px;
            background: var(--bg-primary);
            border: 2px solid var(--border);
            border-radius: 12px;
            transition: all 0.3s;
            position: relative;
        }
        
        .harness-step.active {
            border-color: var(--accent-cyan);
            background: rgba(6, 182, 212, 0.1);
            box-shadow: 0 0 30px rgba(6, 182, 212, 0.2);
        }
        
        .harness-step.completed {
            border-color: var(--accent-green);
            background: rgba(16, 185, 129, 0.05);
        }
        
        .harness-step .icon {
            font-size: 2rem;
            margin-bottom: 8px;
        }
        
        .harness-step .label {
            font-weight: 600;
            font-size: 0.9rem;
        }
        
        .harness-step .status {
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: 4px;
        }
        
        .harness-arrow {
            color: var(--text-dim);
            font-size: 1.5rem;
        }
        
        /* Investigation Log */
        .log-container {
            background: var(--bg-primary);
            border-radius: 8px;
            max-height: 500px;
            overflow-y: auto;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
        }
        
        .log-entry {
            padding: 12px 16px;
            border-bottom: 1px solid var(--border);
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        .log-entry.think { border-left: 3px solid var(--accent-yellow); }
        .log-entry.act { border-left: 3px solid var(--accent-green); }
        .log-entry.observe { border-left: 3px solid var(--accent-cyan); }
        .log-entry.evaluate { border-left: 3px solid var(--accent-purple); }
        .log-entry.llm { border-left: 3px solid var(--accent-blue); background: rgba(59, 130, 246, 0.05); }
        .log-entry.tool { border-left: 3px solid var(--accent-cyan); background: rgba(6, 182, 212, 0.05); }
        .log-entry.finding { border-left: 3px solid var(--accent-yellow); background: rgba(245, 158, 11, 0.05); }
        .log-entry.result { border-left: 3px solid var(--accent-green); background: rgba(16, 185, 129, 0.1); }
        
        .log-phase {
            font-weight: 600;
            margin-bottom: 4px;
        }
        
        .log-content {
            color: var(--text-secondary);
        }
        
        .log-reasoning {
            margin-top: 8px;
            padding: 10px;
            background: var(--bg-secondary);
            border-radius: 6px;
            font-size: 0.8rem;
            color: var(--text-dim);
        }
        
        /* Confidence Meter */
        .confidence-section {
            display: none;
        }
        
        .confidence-section.visible {
            display: block;
        }
        
        .confidence-bar-container {
            background: var(--bg-primary);
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            position: relative;
            margin: 20px 0;
        }
        
        .confidence-bar {
            height: 100%;
            background: linear-gradient(90deg, var(--accent-red), var(--accent-yellow), var(--accent-green));
            transition: width 0.5s ease;
            border-radius: 10px;
        }
        
        .confidence-value {
            position: absolute;
            right: 10px;
            top: 50%;
            transform: translateY(-50%);
            font-weight: 700;
            font-size: 0.9rem;
        }
        
        .thresholds {
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            font-size: 0.75rem;
            color: var(--text-dim);
        }
        
        .threshold-marker {
            text-align: center;
        }
        
        .threshold-marker.active {
            color: var(--accent-green);
        }
        
        /* Resolution Box */
        .resolution-box {
            display: none;
            margin-top: 20px;
            padding: 20px;
            background: linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(6, 182, 212, 0.1));
            border: 1px solid var(--accent-green);
            border-radius: 12px;
        }
        
        .resolution-box.visible {
            display: block;
        }
        
        .resolution-title {
            font-size: 1.1rem;
            font-weight: 600;
            color: var(--accent-green);
            margin-bottom: 12px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        
        .resolution-action {
            font-size: 0.95rem;
            margin-bottom: 8px;
        }
        
        .resolution-command {
            background: var(--bg-primary);
            padding: 12px;
            border-radius: 6px;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.85rem;
            color: var(--accent-cyan);
            margin-top: 10px;
        }
        
        /* Iteration Badge */
        .iteration-badge {
            display: inline-block;
            padding: 4px 12px;
            background: var(--bg-secondary);
            border: 1px solid var(--border);
            border-radius: 20px;
            font-size: 0.8rem;
            color: var(--text-secondary);
            margin-bottom: 15px;
        }
        
        /* Stats Grid */
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(4, 1fr);
            gap: 15px;
            margin-top: 20px;
        }
        
        .stat-card {
            background: var(--bg-primary);
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 1.5rem;
            font-weight: 700;
            color: var(--accent-cyan);
        }
        
        .stat-label {
            font-size: 0.75rem;
            color: var(--text-dim);
            margin-top: 4px;
        }
        
        /* Responsive */
        @media (max-width: 768px) {
            .harness-container { flex-direction: column; }
            .harness-arrow { transform: rotate(90deg); }
            .stats-grid { grid-template-columns: repeat(2, 1fr); }
        }
    </style>
</head>
<body>
    <header>
        <div class="logo">🤖 HACI</div>
        <div class="tagline">Harness-Enhanced Agentic Collaborative Intelligence</div>
        <div class="provider-badge" id="provider-badge">Initializing...</div>
    </header>
    
    <div class="container">
        <!-- Ticket Input -->
        <div class="card">
            <div class="card-title">🎫 Support Ticket</div>
            <input type="text" id="ticket-input" class="ticket-input" 
                   value="API returning 502 errors intermittently for /api/users endpoint. Started ~10 minutes ago. Affecting approximately 25% of requests."
                   placeholder="Describe the issue...">
            <button id="submit-btn" class="btn" onclick="startInvestigation()">
                🔍 Start Investigation
            </button>
        </div>
        
        <!-- Harness Visualization -->
        <div class="card">
            <div class="card-title">⚙️ Harness Loop</div>
            <div id="iteration-badge" class="iteration-badge" style="display:none;">Iteration 1/5</div>
            <div class="harness-container">
                <div class="harness-step" id="step-think">
                    <div class="icon">🧠</div>
                    <div class="label">THINK</div>
                    <div class="status">Form hypotheses</div>
                </div>
                <div class="harness-arrow">→</div>
                <div class="harness-step" id="step-act">
                    <div class="icon">⚡</div>
                    <div class="label">ACT</div>
                    <div class="status">Execute tools</div>
                </div>
                <div class="harness-arrow">→</div>
                <div class="harness-step" id="step-observe">
                    <div class="icon">👁️</div>
                    <div class="label">OBSERVE</div>
                    <div class="status">Analyze data</div>
                </div>
                <div class="harness-arrow">→</div>
                <div class="harness-step" id="step-evaluate">
                    <div class="icon">✅</div>
                    <div class="label">EVALUATE</div>
                    <div class="status">Assess confidence</div>
                </div>
            </div>
        </div>
        
        <!-- Confidence Meter -->
        <div class="card confidence-section" id="confidence-section">
            <div class="card-title">📊 Confidence Assessment</div>
            <div class="confidence-bar-container">
                <div class="confidence-bar" id="confidence-bar" style="width: 0%"></div>
                <div class="confidence-value" id="confidence-value">0%</div>
            </div>
            <div class="thresholds">
                <div class="threshold-marker" id="thresh-continue">
                    <div>🔴 &lt;70%</div>
                    <div>Continue</div>
                </div>
                <div class="threshold-marker" id="thresh-approval">
                    <div>🟠 70%+</div>
                    <div>Require Approval</div>
                </div>
                <div class="threshold-marker" id="thresh-review">
                    <div>🟡 85%+</div>
                    <div>Execute + Review</div>
                </div>
                <div class="threshold-marker" id="thresh-auto">
                    <div>🟢 95%+</div>
                    <div>Auto-Execute</div>
                </div>
            </div>
        </div>
        
        <!-- Investigation Log -->
        <div class="card">
            <div class="card-title">📋 Investigation Log</div>
            <div class="log-container" id="log-container">
                <div class="log-entry" style="color: var(--text-dim);">
                    Click "Start Investigation" to begin the demo...
                </div>
            </div>
        </div>
        
        <!-- Resolution -->
        <div class="resolution-box" id="resolution-box">
            <div class="resolution-title">🎯 Root Cause Identified</div>
            <div id="root-cause"></div>
            <div class="resolution-action" id="resolution-action"></div>
            <div class="resolution-command" id="resolution-command"></div>
        </div>
        
        <!-- Stats -->
        <div class="stats-grid" id="stats-grid" style="display: none;">
            <div class="stat-card">
                <div class="stat-value" id="stat-iterations">0</div>
                <div class="stat-label">Iterations</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-llm-calls">0</div>
                <div class="stat-label">LLM Calls</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-tools">0</div>
                <div class="stat-label">Tools Used</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="stat-findings">0</div>
                <div class="stat-label">Findings</div>
            </div>
        </div>
    </div>
    
    <script>
        let stats = { iterations: 0, llmCalls: 0, tools: 0, findings: 0 };
        
        // Check LLM provider on load
        fetch('/provider').then(r => r.json()).then(data => {
            const badge = document.getElementById('provider-badge');
            if (data.provider === 'anthropic') {
                badge.textContent = '✓ Using Claude (Anthropic)';
                badge.style.color = '#10b981';
            } else if (data.provider === 'openai') {
                badge.textContent = '✓ Using GPT-4 (OpenAI)';
                badge.style.color = '#10b981';
            } else {
                badge.textContent = '⚠ Demo Mode (No API Key)';
                badge.style.color = '#f59e0b';
            }
        });
        
        async function startInvestigation() {
            const ticket = document.getElementById('ticket-input').value;
            const logContainer = document.getElementById('log-container');
            const submitBtn = document.getElementById('submit-btn');
            
            // Reset UI
            logContainer.innerHTML = '';
            submitBtn.disabled = true;
            stats = { iterations: 0, llmCalls: 0, tools: 0, findings: 0 };
            document.getElementById('stats-grid').style.display = 'grid';
            document.getElementById('confidence-section').classList.add('visible');
            document.getElementById('resolution-box').classList.remove('visible');
            document.getElementById('iteration-badge').style.display = 'inline-block';
            resetHarnessSteps();
            updateStats();
            
            try {
                const response = await fetch('/investigate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ ticket })
                });
                
                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    
                    const text = decoder.decode(value);
                    const lines = text.split('\\n').filter(line => line.startsWith('data: '));
                    
                    for (const line of lines) {
                        try {
                            const data = JSON.parse(line.slice(6));
                            handleEvent(data);
                        } catch (e) {}
                    }
                }
            } catch (error) {
                addLogEntry('error', 'Error', error.message);
            } finally {
                submitBtn.disabled = false;
            }
        }
        
        function handleEvent(data) {
            const { type, phase, message, content, confidence, resolution, root_cause, iteration } = data;
            
            // Update iteration badge
            if (iteration) {
                document.getElementById('iteration-badge').textContent = `Iteration ${iteration}/5`;
            }
            
            // Update harness steps
            if (['think', 'act', 'observe', 'evaluate'].includes(type)) {
                setActiveStep(type);
            }
            
            // Add log entry
            if (message) {
                addLogEntry(type, phase || type.toUpperCase(), message, content);
            }
            
            // Update stats
            if (type === 'llm') stats.llmCalls++;
            if (type === 'tool') stats.tools++;
            if (type === 'finding') stats.findings++;
            if (type === 'iteration') stats.iterations = iteration;
            updateStats();
            
            // Update confidence
            if (confidence !== undefined) {
                updateConfidence(confidence);
            }
            
            // Show resolution
            if (type === 'complete' && resolution) {
                showResolution(root_cause, resolution);
            }
        }
        
        function addLogEntry(type, phase, message, content) {
            const logContainer = document.getElementById('log-container');
            const entry = document.createElement('div');
            entry.className = `log-entry ${type}`;
            
            let html = `<div class="log-phase">${getPhaseIcon(type)} ${phase}</div>`;
            html += `<div class="log-content">${message}</div>`;
            
            if (content && content.reasoning) {
                html += `<div class="log-reasoning">💭 ${content.reasoning}</div>`;
            }
            
            entry.innerHTML = html;
            logContainer.appendChild(entry);
            logContainer.scrollTop = logContainer.scrollHeight;
        }
        
        function getPhaseIcon(type) {
            const icons = {
                think: '🧠', act: '⚡', observe: '👁️', evaluate: '✅',
                llm: '🤖', tool: '🔧', finding: '🔍', result: '✓', error: '❌'
            };
            return icons[type] || '•';
        }
        
        function setActiveStep(step) {
            document.querySelectorAll('.harness-step').forEach(el => {
                el.classList.remove('active');
            });
            const stepEl = document.getElementById(`step-${step}`);
            if (stepEl) {
                stepEl.classList.add('active');
            }
        }
        
        function resetHarnessSteps() {
            document.querySelectorAll('.harness-step').forEach(el => {
                el.classList.remove('active', 'completed');
            });
        }
        
        function updateConfidence(value) {
            document.getElementById('confidence-bar').style.width = `${value}%`;
            document.getElementById('confidence-value').textContent = `${value}%`;
            
            // Update threshold markers
            document.getElementById('thresh-continue').classList.toggle('active', value < 70);
            document.getElementById('thresh-approval').classList.toggle('active', value >= 70 && value < 85);
            document.getElementById('thresh-review').classList.toggle('active', value >= 85 && value < 95);
            document.getElementById('thresh-auto').classList.toggle('active', value >= 95);
        }
        
        function updateStats() {
            document.getElementById('stat-iterations').textContent = stats.iterations;
            document.getElementById('stat-llm-calls').textContent = stats.llmCalls;
            document.getElementById('stat-tools').textContent = stats.tools;
            document.getElementById('stat-findings').textContent = stats.findings;
        }
        
        function showResolution(rootCause, resolution) {
            const box = document.getElementById('resolution-box');
            document.getElementById('root-cause').textContent = rootCause || 'Root cause identified';
            document.getElementById('resolution-action').textContent = `Action: ${resolution.immediate_action || 'See command below'}`;
            document.getElementById('resolution-command').textContent = `$ ${resolution.command || 'N/A'}`;
            box.classList.add('visible');
        }
    </script>
</body>
</html>'''


# =============================================================================
# API ROUTES
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML_TEMPLATE


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.get("/provider")
async def get_provider():
    llm = LLMClient()
    return {"provider": llm.provider}


@app.post("/investigate")
async def investigate(request: Request):
    data = await request.json()
    ticket = data.get("ticket", "Unknown issue")
    
    async def generate_events() -> AsyncGenerator[str, None]:
        harness = HACIHarness()
        harness.verbose = False  # Disable console output
        
        state = HarnessState(ticket=ticket)
        
        for iteration in range(state.max_iterations):
            state.iteration = iteration
            yield f'data: {json.dumps({"type": "iteration", "iteration": iteration + 1})}\n\n'
            await asyncio.sleep(0.2)
            
            # THINK
            yield f'data: {json.dumps({"type": "think", "phase": "THINK", "message": "Forming hypotheses..."})}\n\n'
            await asyncio.sleep(0.3)
            
            state = await harness.think(state)
            
            if state.llm_calls:
                last_call = state.llm_calls[-1]
                yield f'data: {json.dumps({"type": "llm", "phase": "LLM", "message": "Generated hypotheses", "content": last_call.get("response", {})})}\n\n'
            
            for h in state.hypotheses[-3:]:
                yield f'data: {json.dumps({"type": "finding", "phase": "Hypothesis", "message": f"{h.get(\'hypothesis\', \'Unknown\')} (Confidence: {h.get(\'confidence\', 0)}%)"})}\n\n'
                await asyncio.sleep(0.1)
            
            # ACT
            yield f'data: {json.dumps({"type": "act", "phase": "ACT", "message": "Executing tools..."})}\n\n'
            await asyncio.sleep(0.2)
            
            prev_tool_count = len(state.tool_results)
            state = await harness.act(state)
            
            for tool_result in state.tool_results[prev_tool_count:]:
                yield f'data: {json.dumps({"type": "tool", "phase": f"Tool: {tool_result[\'tool\']}", "message": tool_result.get(\'summary\', \'Executed\')})}\n\n'
                await asyncio.sleep(0.15)
            
            # OBSERVE
            yield f'data: {json.dumps({"type": "observe", "phase": "OBSERVE", "message": "Analyzing collected data..."})}\n\n'
            await asyncio.sleep(0.3)
            
            prev_finding_count = len(state.findings)
            state = await harness.observe(state)
            
            if state.llm_calls:
                last_call = state.llm_calls[-1]
                yield f'data: {json.dumps({"type": "llm", "phase": "LLM", "message": "Analyzed evidence", "content": last_call.get("response", {})})}\n\n'
            
            for finding in state.findings[prev_finding_count:]:
                severity = finding.get('severity', 'medium').upper()
                yield f'data: {json.dumps({"type": "finding", "phase": f"Finding [{severity}]", "message": finding.get(\'finding\', \'Unknown\')})}\n\n'
                await asyncio.sleep(0.1)
            
            # EVALUATE
            yield f'data: {json.dumps({"type": "evaluate", "phase": "EVALUATE", "message": "Assessing confidence level..."})}\n\n'
            await asyncio.sleep(0.3)
            
            state = await harness.evaluate(state)
            
            if state.llm_calls:
                last_call = state.llm_calls[-1]
                yield f'data: {json.dumps({"type": "llm", "phase": "LLM", "message": f"Confidence: {state.confidence}%", "content": last_call.get("response", {})})}\n\n'
            
            yield f'data: {json.dumps({"type": "confidence", "confidence": state.confidence})}\n\n'
            
            # Determine action
            if state.confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
                action = "🟢 AUTO-EXECUTE"
            elif state.confidence >= CONFIDENCE_THRESHOLDS["execute_review"]:
                action = "🟡 EXECUTE WITH REVIEW"
            elif state.confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
                action = "🟠 REQUIRE APPROVAL"
            else:
                action = "🔴 CONTINUE INVESTIGATION"
            
            yield f'data: {json.dumps({"type": "result", "phase": "Action", "message": f"{action} (Confidence: {state.confidence}%)"})}\n\n'
            
            if state.confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
                break
            
            await asyncio.sleep(0.5)
        
        # Final result
        yield f'data: {json.dumps({"type": "complete", "confidence": state.confidence, "root_cause": state.root_cause, "resolution": state.resolution})}\n\n'
    
    return StreamingResponse(generate_events(), media_type="text/event-stream")


if __name__ == "__main__":
    port = int(os.environ.get("DEMO_PORT", 8080))
    print(f"\n🚀 HACI Demo running at http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
