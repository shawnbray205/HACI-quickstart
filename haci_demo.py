"""
HACI Enhanced Quick Start Demo
==============================
A comprehensive demonstration of the HACI harness pattern with real LLM integration.

This demo shows:
- Real LLM reasoning (Claude/GPT)
- The THINK→ACT→OBSERVE→EVALUATE loop
- Confidence-based action gating
- Multi-agent coordination
- Tool execution with explanations

Run with:
    export ANTHROPIC_API_KEY="your-key"
    python haci_demo.py
"""

import asyncio
import os
import sys
import json
from typing import TypedDict, Literal, List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import textwrap

# =============================================================================
# CONFIGURATION
# =============================================================================

class Colors:
    """ANSI color codes for terminal output."""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    
    # Harness phases
    THINK = "\033[93m"      # Yellow
    ACT = "\033[92m"        # Green
    OBSERVE = "\033[96m"    # Cyan
    EVALUATE = "\033[95m"   # Magenta
    
    # Status
    SUCCESS = "\033[92m"    # Green
    WARNING = "\033[93m"    # Yellow
    ERROR = "\033[91m"      # Red
    INFO = "\033[94m"       # Blue
    
    # Agents
    AGENT = "\033[35m"      # Purple
    TOOL = "\033[36m"       # Cyan
    LLM = "\033[33m"        # Orange/Yellow


CONFIDENCE_THRESHOLDS = {
    "auto_execute": 95,
    "execute_review": 85,
    "require_approval": 70,
}


# =============================================================================
# MOCK MONITORING DATA (Simulated tool responses)
# =============================================================================

MOCK_DATA = {
    "datadog_logs": {
        "query": "service:api-gateway status:error",
        "results": [
            {"timestamp": "2024-01-15T14:20:01Z", "level": "INFO", "message": "Deployment abc123 started", "service": "deploy-manager"},
            {"timestamp": "2024-01-15T14:20:45Z", "level": "INFO", "message": "Deployment abc123 completed successfully", "service": "deploy-manager"},
            {"timestamp": "2024-01-15T14:21:03Z", "level": "WARN", "message": "Connection pool exhausted, waiting for available connection", "service": "api-gateway"},
            {"timestamp": "2024-01-15T14:21:15Z", "level": "ERROR", "message": "HTTP 502 Bad Gateway - upstream connection timeout", "service": "api-gateway", "path": "/api/users", "duration_ms": 30000},
            {"timestamp": "2024-01-15T14:21:16Z", "level": "ERROR", "message": "HTTP 502 Bad Gateway - upstream connection timeout", "service": "api-gateway", "path": "/api/orders", "duration_ms": 30000},
            {"timestamp": "2024-01-15T14:21:18Z", "level": "ERROR", "message": "HTTP 502 Bad Gateway - upstream connection timeout", "service": "api-gateway", "path": "/api/users", "duration_ms": 30000},
            {"timestamp": "2024-01-15T14:22:30Z", "level": "ERROR", "message": "Database connection timeout after 30s", "service": "user-service"},
            {"timestamp": "2024-01-15T14:23:00Z", "level": "ERROR", "message": "Circuit breaker OPEN for user-service", "service": "api-gateway"},
        ],
        "summary": {
            "total_errors": 47,
            "error_rate": "23.5%",
            "first_error": "2024-01-15T14:21:15Z",
            "services_affected": ["api-gateway", "user-service"],
        }
    },
    "github_deployments": {
        "recent": [
            {
                "id": "abc123",
                "timestamp": "2024-01-15T14:20:00Z",
                "author": "developer@company.com",
                "environment": "production",
                "status": "success",
                "commit_sha": "a1b2c3d4",
                "commit_message": "Reduce connection pool for cost savings",
                "files_changed": [
                    {"path": "config/database.yaml", "changes": "pool_size: 10 → pool_size: 5"},
                    {"path": "config/timeouts.yaml", "changes": "connection_timeout: 30s → connection_timeout: 10s"},
                ],
            }
        ]
    },
    "prometheus_metrics": {
        "api_gateway": {
            "cpu_percent": 45.2,
            "memory_percent": 78.5,
            "active_connections": 98,
            "max_connections": 100,
            "connection_wait_time_p99": 4500,
            "request_latency_p99": 2800,
        },
        "database": {
            "active_connections": 5,
            "max_connections": 5,
            "query_latency_p99": 850,
            "connection_pool_exhausted_count": 127,
        }
    },
    "pagerduty_incidents": {
        "active": [
            {
                "id": "INC-4521",
                "title": "High error rate on api-gateway",
                "severity": "P2",
                "created_at": "2024-01-15T14:25:00Z",
                "status": "triggered",
            }
        ]
    }
}


# =============================================================================
# LLM CLIENT
# =============================================================================

class LLMClient:
    """Unified LLM client supporting Anthropic and OpenAI."""
    
    def __init__(self):
        self.provider = None
        self.client = None
        self._setup_client()
    
    def _setup_client(self):
        """Initialize the LLM client based on available API keys."""
        if os.environ.get("ANTHROPIC_API_KEY"):
            try:
                from anthropic import Anthropic
                self.client = Anthropic()
                self.provider = "anthropic"
                return
            except ImportError:
                pass
        
        if os.environ.get("OPENAI_API_KEY"):
            try:
                from openai import OpenAI
                self.client = OpenAI()
                self.provider = "openai"
                return
            except ImportError:
                pass
        
        self.provider = "mock"
    
    async def generate(self, system: str, prompt: str, max_tokens: int = 1024) -> str:
        """Generate a response from the LLM."""
        if self.provider == "anthropic":
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text
        
        elif self.provider == "openai":
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                max_tokens=max_tokens,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        
        else:
            return self._mock_response(prompt)
    
    def _mock_response(self, prompt: str) -> str:
        """Generate mock responses for demo mode."""
        if "hypotheses" in prompt.lower():
            return json.dumps({
                "hypotheses": [
                    {"hypothesis": "Recent deployment changed connection pool configuration", "confidence": 75, "evidence_needed": ["deployment logs", "config changes"]},
                    {"hypothesis": "Database connection exhaustion due to reduced pool size", "confidence": 60, "evidence_needed": ["db metrics", "connection counts"]},
                    {"hypothesis": "Upstream service failure causing cascading timeouts", "confidence": 45, "evidence_needed": ["service health", "dependency graph"]}
                ],
                "next_actions": ["Query deployment history", "Check database connection metrics"],
                "reasoning": "The timing of errors starting at 14:21 suggests a recent change triggered this issue. The 502 errors indicate upstream connectivity problems. Need to correlate with deployment timeline and check connection pool status."
            })
        elif "analyze" in prompt.lower() or "findings" in prompt.lower():
            return json.dumps({
                "findings": [
                    {"finding": "Deployment abc123 at 14:20 reduced connection pool from 10 to 5", "severity": "critical", "confidence": 98},
                    {"finding": "Database connections at 100% capacity (5/5 active)", "severity": "critical", "confidence": 96},
                    {"finding": "Connection wait time spiked to 4.5s (p99) after deployment", "severity": "high", "confidence": 94},
                    {"finding": "47 HTTP 502 errors occurred in 1 hour, all after 14:21", "severity": "high", "confidence": 99}
                ],
                "patterns": [
                    "Error spike correlates exactly with deployment completion time",
                    "All affected services share the same database connection pool",
                    "Circuit breaker activation indicates sustained connection failures"
                ],
                "correlations": [
                    "Deployment abc123 (14:20) → Connection pool exhaustion (14:21) → 502 errors (14:21+)",
                    "pool_size reduction 10→5 matches current max_connections=5"
                ],
                "reasoning": "Clear causal chain: deployment reduced pool_size from 10 to 5, but normal traffic requires 8-10 connections. This immediately caused pool exhaustion and upstream timeouts."
            })
        elif "resolution" in prompt.lower() or "evaluate" in prompt.lower():
            return json.dumps({
                "root_cause_identified": True,
                "root_cause": "Connection pool misconfiguration in deployment abc123 reduced pool_size from 10 to 5, causing immediate exhaustion under normal load",
                "confidence": 94,
                "resolution": {
                    "immediate_action": "Rollback deployment abc123 to restore pool_size=10",
                    "command": "kubectl rollout undo deployment/api-gateway --to-revision=previous",
                    "expected_recovery_time": "2-3 minutes after rollback",
                    "risk_level": "low"
                },
                "alternative_actions": [
                    {"action": "Hot-patch pool_size to 15 via ConfigMap", "risk": "medium"},
                    {"action": "Scale api-gateway horizontally to distribute load", "risk": "low"}
                ],
                "reasoning": "High confidence in root cause due to perfect temporal correlation and matching configuration values. Rollback is safest option as it restores known-good state."
            })
        return json.dumps({"response": "Analysis in progress..."})


# =============================================================================
# TOOLS (Simulated integrations)
# =============================================================================

class Tool:
    """Base class for HACI tools."""
    name: str
    description: str
    
    async def execute(self, **params) -> Dict[str, Any]:
        raise NotImplementedError


class DatadogLogsTool(Tool):
    name = "datadog_logs_search"
    description = "Search application logs in Datadog"
    
    async def execute(self, query: str, timeframe: str = "1h") -> Dict[str, Any]:
        await asyncio.sleep(0.5)
        return MOCK_DATA["datadog_logs"]


class GitHubDeploymentsTool(Tool):
    name = "github_deployments"
    description = "Get recent deployments from GitHub"
    
    async def execute(self, repo: str = "main-service", limit: int = 5) -> Dict[str, Any]:
        await asyncio.sleep(0.3)
        return MOCK_DATA["github_deployments"]


class PrometheusMetricsTool(Tool):
    name = "prometheus_metrics"
    description = "Query infrastructure metrics from Prometheus"
    
    async def execute(self, service: str, metrics: List[str] = None) -> Dict[str, Any]:
        await asyncio.sleep(0.3)
        return MOCK_DATA["prometheus_metrics"]


class PagerDutyTool(Tool):
    name = "pagerduty_incidents"
    description = "Get active incidents from PagerDuty"
    
    async def execute(self) -> Dict[str, Any]:
        await asyncio.sleep(0.2)
        return MOCK_DATA["pagerduty_incidents"]


# =============================================================================
# HARNESS STATE
# =============================================================================

@dataclass
class HarnessState:
    """State maintained throughout the investigation."""
    ticket: str
    iteration: int = 0
    max_iterations: int = 5
    
    hypotheses: List[Dict] = field(default_factory=list)
    findings: List[Dict] = field(default_factory=list)
    tool_results: List[Dict] = field(default_factory=list)
    
    confidence: float = 0.0
    resolution: Optional[Dict] = None
    root_cause: Optional[str] = None
    status: str = "investigating"
    
    llm_calls: List[Dict] = field(default_factory=list)


# =============================================================================
# HARNESS IMPLEMENTATION
# =============================================================================

class HACIHarness:
    """
    The HACI Harness implements the THINK→ACT→OBSERVE→EVALUATE loop.
    """
    
    def __init__(self):
        self.llm = LLMClient()
        self.tools = {
            "datadog_logs_search": DatadogLogsTool(),
            "github_deployments": GitHubDeploymentsTool(),
            "prometheus_metrics": PrometheusMetricsTool(),
            "pagerduty_incidents": PagerDutyTool(),
        }
    
    def _header(self, text: str, char: str = "═", color: str = Colors.INFO):
        """Print a header."""
        width = 70
        print(f"\n{color}{char * width}{Colors.RESET}")
        print(f"{color}{Colors.BOLD}  {text}{Colors.RESET}")
        print(f"{color}{char * width}{Colors.RESET}")
    
    def _phase_header(self, phase: str, icon: str, color: str):
        """Print a phase header."""
        print(f"\n{color}{'─' * 60}{Colors.RESET}")
        print(f"{color}{Colors.BOLD}  {icon}  {phase}{Colors.RESET}")
        print(f"{color}{'─' * 60}{Colors.RESET}")
    
    def _show_llm_call(self, phase: str, prompt_preview: str, response: Dict):
        """Display LLM interaction details."""
        print(f"\n{Colors.LLM}  🤖 LLM Call ({self.llm.provider.upper()}):{Colors.RESET}")
        print(f"{Colors.DIM}  ┌─ Phase: {phase}{Colors.RESET}")
        print(f"{Colors.DIM}  ├─ Prompt: \"{prompt_preview[:50]}...\"{Colors.RESET}")
        
        if "reasoning" in response:
            print(f"{Colors.DIM}  ├─ Reasoning:{Colors.RESET}")
            reasoning_lines = textwrap.wrap(response["reasoning"], width=60)
            for line in reasoning_lines[:3]:
                print(f"{Colors.DIM}  │    {line}{Colors.RESET}")
        
        print(f"{Colors.DIM}  └─ Response keys: {list(response.keys())}{Colors.RESET}")
    
    async def think(self, state: HarnessState) -> HarnessState:
        """THINK: Form hypotheses and plan investigation."""
        self._phase_header("THINK - Forming Hypotheses", "🧠", Colors.THINK)
        
        context = {
            "ticket": state.ticket,
            "iteration": state.iteration,
            "previous_findings": state.findings[-3:] if state.findings else [],
        }
        
        system_prompt = """You are a HACI Investigation Agent. Form hypotheses about the root cause.
Respond with JSON: {"hypotheses": [{"hypothesis": "...", "confidence": 0-100, "evidence_needed": [...]}], "next_actions": [...], "reasoning": "..."}"""
        
        user_prompt = f"""Investigate this ticket (iteration {state.iteration + 1}):
TICKET: {state.ticket}
PREVIOUS FINDINGS: {json.dumps(context['previous_findings'], indent=2)}

Form hypotheses about what's causing this issue."""
        
        print(f"\n{Colors.DIM}  Sending context to LLM for hypothesis generation...{Colors.RESET}")
        
        response_text = await self.llm.generate(system_prompt, user_prompt)
        response = json.loads(response_text) if response_text.startswith("{") else {"hypotheses": [], "reasoning": response_text}
        
        state.llm_calls.append({"phase": "THINK", "response": response})
        self._show_llm_call("THINK", user_prompt, response)
        
        if response.get("hypotheses"):
            print(f"\n{Colors.THINK}  📊 Hypotheses Generated:{Colors.RESET}")
            for i, h in enumerate(response["hypotheses"], 1):
                conf = h.get("confidence", 50)
                bar = "█" * (conf // 10) + "░" * (10 - conf // 10)
                print(f"\n     {i}. {h['hypothesis']}")
                print(f"        Confidence: {Colors.BOLD}[{bar}] {conf}%{Colors.RESET}")
                if h.get("evidence_needed"):
                    print(f"        Evidence needed: {', '.join(h['evidence_needed'])}")
            state.hypotheses.extend(response["hypotheses"])
        
        if response.get("next_actions"):
            print(f"\n{Colors.THINK}  📋 Next Actions Planned:{Colors.RESET}")
            for action in response["next_actions"]:
                print(f"     → {action}")
        
        return state
    
    async def act(self, state: HarnessState) -> HarnessState:
        """ACT: Execute tools to gather evidence."""
        self._phase_header("ACT - Gathering Evidence", "⚡", Colors.ACT)
        
        # Select tools based on iteration
        if state.iteration == 0:
            tools_to_run = [
                ("datadog_logs_search", {"query": "service:api-gateway status:error", "timeframe": "1h"}),
                ("pagerduty_incidents", {}),
            ]
        elif state.iteration == 1:
            tools_to_run = [
                ("github_deployments", {"repo": "main-service", "limit": 5}),
                ("prometheus_metrics", {"service": "api-gateway"}),
            ]
        else:
            tools_to_run = [("prometheus_metrics", {"service": "database"})]
        
        print(f"\n{Colors.ACT}  Executing {len(tools_to_run)} integration(s)...{Colors.RESET}")
        
        for tool_name, params in tools_to_run:
            tool = self.tools.get(tool_name)
            if not tool:
                continue
            
            print(f"\n{Colors.TOOL}  🔧 Tool: {tool_name}{Colors.RESET}")
            print(f"{Colors.DIM}     ├─ Description: {tool.description}{Colors.RESET}")
            print(f"{Colors.DIM}     ├─ Parameters: {json.dumps(params)}{Colors.RESET}")
            print(f"{Colors.DIM}     ├─ Executing...{Colors.RESET}")
            
            result = await tool.execute(**params)
            
            # Create summary
            if "results" in result:
                summary = f"Found {len(result['results'])} log entries"
                if result.get("summary"):
                    summary += f" | {result['summary'].get('total_errors', 0)} errors | Error rate: {result['summary'].get('error_rate', 'N/A')}"
            elif "recent" in result:
                dep = result["recent"][0] if result["recent"] else {}
                summary = f"Found deployment {dep.get('id', 'N/A')} at {dep.get('timestamp', 'N/A')}"
                if dep.get("files_changed"):
                    summary += f" | Changed: {', '.join(f['path'] for f in dep['files_changed'])}"
            elif "api_gateway" in result:
                metrics = result["api_gateway"]
                summary = f"CPU: {metrics.get('cpu_percent', 0)}% | Mem: {metrics.get('memory_percent', 0)}% | Connections: {metrics.get('active_connections', 0)}/{metrics.get('max_connections', 0)}"
            elif "active" in result:
                summary = f"Found {len(result['active'])} active incident(s)"
            else:
                summary = f"Retrieved {len(result)} data points"
            
            print(f"{Colors.DIM}     └─ Result: {summary}{Colors.RESET}")
            
            state.tool_results.append({
                "tool": tool_name,
                "params": params,
                "result": result,
                "summary": summary
            })
        
        return state
    
    async def observe(self, state: HarnessState) -> HarnessState:
        """OBSERVE: Analyze evidence and extract findings."""
        self._phase_header("OBSERVE - Analyzing Evidence", "👁️", Colors.OBSERVE)
        
        recent_results = state.tool_results[-4:]
        
        system_prompt = """You are a HACI Observation Agent. Analyze the data and extract findings.
Respond with JSON: {"findings": [{"finding": "...", "severity": "critical|high|medium|low", "confidence": 0-100}], "patterns": [...], "correlations": [...], "reasoning": "..."}"""
        
        user_prompt = f"""Analyze this data for the investigation:
TICKET: {state.ticket}
TOOL OUTPUTS: {json.dumps([{"tool": r["tool"], "result": r["result"]} for r in recent_results], indent=2)}
HYPOTHESES: {json.dumps(state.hypotheses[-3:], indent=2)}

Extract key findings, patterns, and correlations."""
        
        print(f"\n{Colors.DIM}  Sending tool outputs to LLM for analysis...{Colors.RESET}")
        
        response_text = await self.llm.generate(system_prompt, user_prompt)
        response = json.loads(response_text) if response_text.startswith("{") else {"findings": [], "reasoning": response_text}
        
        state.llm_calls.append({"phase": "OBSERVE", "response": response})
        self._show_llm_call("OBSERVE", "Analyze tool outputs", response)
        
        if response.get("findings"):
            print(f"\n{Colors.OBSERVE}  🔍 Findings Extracted:{Colors.RESET}")
            severity_icons = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🟢"}
            for finding in response["findings"]:
                sev = finding.get("severity", "medium")
                icon = severity_icons.get(sev, "⚪")
                conf = finding.get("confidence", 50)
                print(f"\n     {icon} [{sev.upper()}] {finding['finding']}")
                print(f"        Confidence: {conf}%")
            state.findings.extend(response["findings"])
        
        if response.get("correlations"):
            print(f"\n{Colors.OBSERVE}  🔗 Correlations Identified:{Colors.RESET}")
            for corr in response["correlations"]:
                print(f"     • {corr}")
        
        return state
    
    async def evaluate(self, state: HarnessState) -> HarnessState:
        """EVALUATE: Assess confidence and determine action."""
        self._phase_header("EVALUATE - Confidence Assessment", "✅", Colors.EVALUATE)
        
        system_prompt = """You are a HACI Evaluation Agent. Assess if root cause is identified.
Respond with JSON: {"root_cause_identified": true/false, "root_cause": "...", "confidence": 0-100, "resolution": {"immediate_action": "...", "command": "...", "risk_level": "low|medium|high"}, "reasoning": "..."}"""
        
        user_prompt = f"""Evaluate this investigation:
TICKET: {state.ticket}
FINDINGS: {json.dumps(state.findings, indent=2)}
HYPOTHESES: {json.dumps(state.hypotheses, indent=2)}

Is root cause identified? What's the confidence level? What action should be taken?"""
        
        print(f"\n{Colors.DIM}  Sending findings to LLM for evaluation...{Colors.RESET}")
        
        response_text = await self.llm.generate(system_prompt, user_prompt)
        response = json.loads(response_text) if response_text.startswith("{") else {"confidence": 30, "reasoning": response_text}
        
        state.llm_calls.append({"phase": "EVALUATE", "response": response})
        self._show_llm_call("EVALUATE", "Evaluate findings", response)
        
        confidence = response.get("confidence", 30)
        state.confidence = confidence
        state.root_cause = response.get("root_cause")
        state.resolution = response.get("resolution")
        
        # Confidence visualization
        print(f"\n{Colors.EVALUATE}  📊 Confidence Score:{Colors.RESET}")
        bar_len = 40
        filled = int(confidence / 100 * bar_len)
        
        if confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
            color = Colors.SUCCESS
        elif confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
            color = Colors.WARNING
        else:
            color = Colors.ERROR
        
        print(f"     {color}[{'█' * filled}{'░' * (bar_len - filled)}] {confidence}%{Colors.RESET}")
        
        # Threshold markers
        print(f"\n     Confidence Thresholds:")
        for name, threshold in CONFIDENCE_THRESHOLDS.items():
            marker = "✓" if confidence >= threshold else "○"
            label = name.replace("_", " ").title()
            print(f"       {marker} {threshold}% - {label}")
        
        # Action decision
        print(f"\n{Colors.EVALUATE}  ⚡ Action Decision:{Colors.RESET}")
        if confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
            action = f"{Colors.SUCCESS}🟢 AUTO-EXECUTE{Colors.RESET}"
            desc = "Confidence exceeds 95% - action will execute automatically"
            state.status = "auto_executing"
        elif confidence >= CONFIDENCE_THRESHOLDS["execute_review"]:
            action = f"{Colors.WARNING}🟡 EXECUTE WITH REVIEW{Colors.RESET}"
            desc = "Confidence 85-94% - executing with post-action review notification"
            state.status = "executing_with_review"
        elif confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
            action = f"{Colors.WARNING}🟠 REQUIRE APPROVAL{Colors.RESET}"
            desc = "Confidence 70-84% - waiting for human approval"
            state.status = "awaiting_approval"
        else:
            action = f"{Colors.ERROR}🔴 CONTINUE INVESTIGATION{Colors.RESET}"
            desc = "Confidence below 70% - need more evidence"
            state.status = "investigating"
        
        print(f"     {action}")
        print(f"     {Colors.DIM}{desc}{Colors.RESET}")
        
        # Show resolution if identified
        if response.get("root_cause_identified") and state.resolution:
            print(f"\n{Colors.SUCCESS}  🎯 Root Cause:{Colors.RESET}")
            print(f"     {state.root_cause}")
            
            print(f"\n{Colors.SUCCESS}  💡 Recommended Resolution:{Colors.RESET}")
            print(f"     Action: {state.resolution.get('immediate_action', 'N/A')}")
            if state.resolution.get("command"):
                print(f"     Command: {Colors.TOOL}{state.resolution['command']}{Colors.RESET}")
            print(f"     Risk Level: {state.resolution.get('risk_level', 'unknown')}")
            if state.resolution.get("expected_recovery_time"):
                print(f"     Expected Recovery: {state.resolution['expected_recovery_time']}")
        
        state.iteration += 1
        return state
    
    async def run(self, ticket: str) -> HarnessState:
        """Run the complete THINK→ACT→OBSERVE→EVALUATE loop."""
        
        # Header
        print(f"\n{Colors.BOLD}╔{'═' * 68}╗{Colors.RESET}")
        print(f"{Colors.BOLD}║{Colors.RESET}  🤖 HACI - Harness-Enhanced Agentic Collaborative Intelligence       {Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.BOLD}║{Colors.RESET}     Interactive Investigation Demo                                   {Colors.BOLD}║{Colors.RESET}")
        print(f"{Colors.BOLD}╚{'═' * 68}╝{Colors.RESET}")
        
        # LLM provider info
        if self.llm.provider == "anthropic":
            print(f"\n{Colors.SUCCESS}  ✓ LLM Provider: Claude (Anthropic){Colors.RESET}")
        elif self.llm.provider == "openai":
            print(f"\n{Colors.SUCCESS}  ✓ LLM Provider: GPT-4 (OpenAI){Colors.RESET}")
        else:
            print(f"\n{Colors.WARNING}  ⚠ No API key found - using realistic mock responses{Colors.RESET}")
            print(f"{Colors.DIM}    Set ANTHROPIC_API_KEY or OPENAI_API_KEY for live LLM integration{Colors.RESET}")
        
        print(f"\n{Colors.INFO}  🎫 Ticket:{Colors.RESET}")
        print(f"     {ticket}")
        
        # Initialize state
        state = HarnessState(ticket=ticket)
        
        # Run harness loop
        while state.iteration < state.max_iterations:
            self._header(f"HARNESS ITERATION {state.iteration + 1}/{state.max_iterations}", "─", Colors.BOLD)
            
            state = await self.think(state)
            await asyncio.sleep(0.2)
            
            state = await self.act(state)
            await asyncio.sleep(0.2)
            
            state = await self.observe(state)
            await asyncio.sleep(0.2)
            
            state = await self.evaluate(state)
            await asyncio.sleep(0.2)
            
            if state.confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
                break
        
        # Summary
        self._print_summary(state)
        return state
    
    def _print_summary(self, state: HarnessState):
        """Print final investigation summary."""
        self._header("INVESTIGATION SUMMARY", "═", Colors.BOLD)
        
        print(f"\n  📋 Overview:")
        print(f"     Status: {Colors.BOLD}{state.status.upper()}{Colors.RESET}")
        print(f"     Iterations: {state.iteration}")
        print(f"     Confidence: {state.confidence}%")
        print(f"     LLM Calls: {len(state.llm_calls)}")
        print(f"     Tools Used: {len(state.tool_results)}")
        print(f"     Findings: {len(state.findings)}")
        
        if state.findings:
            print(f"\n  🔍 Key Findings:")
            for i, f in enumerate(state.findings[:4], 1):
                print(f"     {i}. [{f.get('severity', 'medium').upper()}] {f['finding']}")
        
        if state.root_cause:
            print(f"\n  {Colors.SUCCESS}🎯 Root Cause:{Colors.RESET}")
            for line in textwrap.wrap(state.root_cause, width=60):
                print(f"     {line}")
        
        if state.resolution:
            print(f"\n  {Colors.SUCCESS}💡 Resolution:{Colors.RESET}")
            print(f"     {state.resolution.get('immediate_action', 'N/A')}")
            if state.resolution.get("command"):
                print(f"     $ {state.resolution['command']}")
        
        # What would happen in production
        print(f"\n  ⚡ Production Behavior (Confidence: {state.confidence}%):")
        if state.confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
            print(f"     {Colors.SUCCESS}→ Would AUTO-EXECUTE the resolution{Colors.RESET}")
        elif state.confidence >= CONFIDENCE_THRESHOLDS["execute_review"]:
            print(f"     {Colors.WARNING}→ Would EXECUTE with team notification for review{Colors.RESET}")
        elif state.confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
            print(f"     {Colors.WARNING}→ Would wait for HUMAN APPROVAL via Slack/email{Colors.RESET}")
        else:
            print(f"     {Colors.ERROR}→ Would ESCALATE to human operator{Colors.RESET}")
        
        print(f"\n{'═' * 70}")
        print(f"  ✅ Demo complete!")
        print(f"  The full HACI system includes 10 specialized agents and 50+ integrations.")
        print(f"{'═' * 70}\n")


# =============================================================================
# MAIN
# =============================================================================

async def main():
    """Run the HACI demo."""
    harness = HACIHarness()
    
    ticket = "API returning 502 errors intermittently for /api/users endpoint. Started approximately 10 minutes ago. Affecting roughly 25% of requests. PagerDuty alert triggered."
    
    await harness.run(ticket)


if __name__ == "__main__":
    asyncio.run(main())
