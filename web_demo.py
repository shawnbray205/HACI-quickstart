"""
HACI Web Demo Server
====================
A simple web interface to demonstrate the HACI harness pattern.
"""

import asyncio
import json
import os
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
import uvicorn

# Import the demo logic
from haci_demo import (
    InvestigationState,
    think_node,
    act_node,
    observe_node,
    evaluate_node,
    CONFIDENCE_THRESHOLDS,
)

app = FastAPI(title="HACI Quick Start Demo")


# =============================================================================
# HTML TEMPLATE
# =============================================================================

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>HACI Quick Start Demo</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
            min-height: 100vh;
            color: #e0e0e0;
            padding: 20px;
        }
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        header {
            text-align: center;
            padding: 30px 0;
        }
        h1 {
            color: #00d9ff;
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #888;
            font-size: 1.1rem;
        }
        .card {
            background: rgba(255,255,255,0.05);
            border-radius: 12px;
            padding: 20px;
            margin: 20px 0;
            border: 1px solid rgba(255,255,255,0.1);
        }
        .card h2 {
            color: #00d9ff;
            margin-bottom: 15px;
            font-size: 1.2rem;
        }
        .ticket-input {
            width: 100%;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid rgba(255,255,255,0.2);
            background: rgba(0,0,0,0.3);
            color: #fff;
            font-size: 1rem;
            margin-bottom: 15px;
        }
        .btn {
            background: linear-gradient(135deg, #00d9ff 0%, #0099cc 100%);
            color: #000;
            border: none;
            padding: 12px 30px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 20px rgba(0,217,255,0.3);
        }
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        #investigation-log {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            line-height: 1.6;
            max-height: 400px;
            overflow-y: auto;
            padding: 15px;
            background: rgba(0,0,0,0.4);
            border-radius: 8px;
        }
        .log-think { color: #ffcc00; }
        .log-act { color: #00ff88; }
        .log-observe { color: #00d9ff; }
        .log-evaluate { color: #ff6b6b; }
        .log-result { color: #88ff88; font-weight: bold; }
        .confidence-bar {
            height: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
        }
        .confidence-fill {
            height: 100%;
            background: linear-gradient(90deg, #ff6b6b, #ffcc00, #00ff88);
            transition: width 0.5s ease;
            border-radius: 10px;
        }
        .harness-diagram {
            display: flex;
            justify-content: space-around;
            align-items: center;
            padding: 20px 0;
            flex-wrap: wrap;
            gap: 10px;
        }
        .harness-step {
            text-align: center;
            padding: 15px 20px;
            border-radius: 8px;
            background: rgba(255,255,255,0.05);
            min-width: 100px;
            transition: all 0.3s;
        }
        .harness-step.active {
            background: rgba(0,217,255,0.2);
            box-shadow: 0 0 20px rgba(0,217,255,0.3);
        }
        .harness-step .icon { font-size: 1.5rem; }
        .harness-step .label { margin-top: 5px; font-size: 0.8rem; }
        .arrow { color: #555; font-size: 1.5rem; }
        #results { display: none; }
        #results.visible { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🤖 HACI Quick Start</h1>
            <p class="subtitle">Harness-Enhanced Agentic Collaborative Intelligence</p>
        </header>
        
        <div class="card">
            <h2>🎫 Submit Investigation</h2>
            <input type="text" id="ticket-input" class="ticket-input" 
                   value="API returning 502 errors intermittently for /api/users endpoint"
                   placeholder="Describe the issue...">
            <button id="submit-btn" class="btn" onclick="startInvestigation()">
                🔍 Start Investigation
            </button>
        </div>
        
        <div class="card">
            <h2>⚙️ Harness Pattern</h2>
            <div class="harness-diagram">
                <div class="harness-step" id="step-think">
                    <div class="icon">🧠</div>
                    <div class="label">THINK</div>
                </div>
                <div class="arrow">→</div>
                <div class="harness-step" id="step-act">
                    <div class="icon">⚡</div>
                    <div class="label">ACT</div>
                </div>
                <div class="arrow">→</div>
                <div class="harness-step" id="step-observe">
                    <div class="icon">👁️</div>
                    <div class="label">OBSERVE</div>
                </div>
                <div class="arrow">→</div>
                <div class="harness-step" id="step-evaluate">
                    <div class="icon">✅</div>
                    <div class="label">EVALUATE</div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <h2>📋 Investigation Log</h2>
            <div id="investigation-log">
                <p style="color: #666;">Click "Start Investigation" to begin...</p>
            </div>
        </div>
        
        <div class="card" id="results">
            <h2>📊 Results</h2>
            <p>Confidence: <span id="confidence-value">0%</span></p>
            <div class="confidence-bar">
                <div class="confidence-fill" id="confidence-fill" style="width: 0%"></div>
            </div>
            <p id="action-recommendation"></p>
            <div id="resolution" style="margin-top: 15px; padding: 15px; background: rgba(0,255,136,0.1); border-radius: 8px;"></div>
        </div>
    </div>
    
    <script>
        async function startInvestigation() {
            const ticket = document.getElementById('ticket-input').value;
            const logDiv = document.getElementById('investigation-log');
            const submitBtn = document.getElementById('submit-btn');
            const resultsDiv = document.getElementById('results');
            
            // Reset UI
            logDiv.innerHTML = '';
            submitBtn.disabled = true;
            resultsDiv.classList.remove('visible');
            clearActiveSteps();
            
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
                        const data = JSON.parse(line.slice(6));
                        handleEvent(data, logDiv);
                    }
                }
            } catch (error) {
                logDiv.innerHTML += `<p style="color: red;">Error: ${error.message}</p>`;
            } finally {
                submitBtn.disabled = false;
            }
        }
        
        function handleEvent(data, logDiv) {
            const { type, message, confidence, resolution, action } = data;
            
            // Update active step
            clearActiveSteps();
            if (['think', 'act', 'observe', 'evaluate'].includes(type)) {
                document.getElementById(`step-${type}`).classList.add('active');
            }
            
            // Add log entry
            const colorClass = `log-${type}`;
            logDiv.innerHTML += `<p class="${colorClass}">${message}</p>`;
            logDiv.scrollTop = logDiv.scrollHeight;
            
            // Update results if complete
            if (type === 'complete') {
                document.getElementById('results').classList.add('visible');
                document.getElementById('confidence-value').textContent = `${confidence}%`;
                document.getElementById('confidence-fill').style.width = `${confidence}%`;
                document.getElementById('action-recommendation').innerHTML = `<strong>Action:</strong> ${action}`;
                document.getElementById('resolution').innerHTML = `<strong>Resolution:</strong><br>${resolution.replace(/\\n/g, '<br>')}`;
            }
        }
        
        function clearActiveSteps() {
            document.querySelectorAll('.harness-step').forEach(el => el.classList.remove('active'));
        }
    </script>
</body>
</html>
"""


# =============================================================================
# API ENDPOINTS
# =============================================================================

@app.get("/", response_class=HTMLResponse)
async def home():
    """Serve the demo UI."""
    return HTML_TEMPLATE


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/investigate")
async def investigate(request: Request):
    """Run an investigation and stream results."""
    data = await request.json()
    ticket = data.get("ticket", "Unknown issue")
    
    async def generate_events() -> AsyncGenerator[str, None]:
        state: InvestigationState = {
            "ticket": ticket,
            "messages": [],
            "hypotheses": [],
            "findings": [],
            "tool_outputs": [],
            "confidence": 0.0,
            "resolution": "",
            "iteration": 0,
            "max_iterations": 5,
        }
        
        # Run harness loop
        for iteration in range(state["max_iterations"]):
            state["iteration"] = iteration
            
            # THINK
            yield f'data: {json.dumps({"type": "think", "message": f"🧠 THINK: Forming hypotheses (iteration {iteration + 1})..."})}\n\n'
            await asyncio.sleep(0.5)
            state = think_node(state)
            
            # ACT
            yield f'data: {json.dumps({"type": "act", "message": f"⚡ ACT: Executing investigation tools..."})}\n\n'
            await asyncio.sleep(0.5)
            state = act_node(state)
            
            # OBSERVE
            finding = state["findings"][-1] if state["findings"] else "Analyzing..."
            yield f'data: {json.dumps({"type": "observe", "message": f"👁️ OBSERVE: {finding}"})}\n\n'
            await asyncio.sleep(0.5)
            state = observe_node(state)
            
            # EVALUATE
            state = evaluate_node(state)
            confidence = state["confidence"]
            
            if confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
                action = "🟢 AUTO-EXECUTE"
            elif confidence >= CONFIDENCE_THRESHOLDS["execute_review"]:
                action = "🟡 EXECUTE WITH REVIEW"
            elif confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
                action = "🟠 REQUIRE APPROVAL"
            else:
                action = "🔴 CONTINUE INVESTIGATION"
            
            yield f'data: {json.dumps({"type": "evaluate", "message": f"✅ EVALUATE: Confidence {confidence}% - {action}"})}\n\n'
            await asyncio.sleep(0.3)
            
            # Check if we should stop
            if confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
                break
        
        # Final result
        yield f'data: {json.dumps({"type": "complete", "confidence": state["confidence"], "resolution": state["resolution"], "action": action})}\n\n'
    
    return StreamingResponse(
        generate_events(),
        media_type="text/event-stream",
    )


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    port = int(os.environ.get("DEMO_PORT", 8080))
    print(f"\n🚀 HACI Quick Start Demo running at http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port)
