"""
HACI Quick Start Demo
=====================
A minimal implementation showing the core harness pattern.

Run with:
    export ANTHROPIC_API_KEY="your-key"
    python haci_demo.py
"""

import asyncio
import os
import sys
from typing import TypedDict, Literal, Annotated, List
from dataclasses import dataclass
from datetime import datetime
import operator

# Check for required dependencies
try:
    from langgraph.graph import StateGraph, START, END
    from langchain_anthropic import ChatAnthropic
    from langchain_core.messages import HumanMessage, AIMessage
except ImportError:
    print("Missing dependencies. Install with:")
    print("  pip install langgraph langchain-anthropic")
    sys.exit(1)


# =============================================================================
# CONFIGURATION
# =============================================================================

CONFIDENCE_THRESHOLDS = {
    "auto_execute": 95,
    "execute_review": 85,
    "require_approval": 70,
}

# Mock data for demonstration
MOCK_DATADOG_LOGS = """
[14:20:01] INFO  Deployment started: abc123
[14:20:45] INFO  Deployment completed: abc123
[14:21:03] WARN  Connection pool exhausted, waiting...
[14:21:15] ERROR HTTP 502 Bad Gateway - /api/users
[14:21:16] ERROR HTTP 502 Bad Gateway - /api/orders  
[14:21:18] ERROR HTTP 502 Bad Gateway - /api/users
[14:22:30] ERROR Connection timeout to database
[14:23:00] ERROR HTTP 502 Bad Gateway - /api/users (47 occurrences in last hour)
"""

MOCK_GITHUB_DEPLOYMENTS = """
Deployment: abc123
  Timestamp: 2024-01-15 14:20:00 UTC
  Author: developer@company.com
  Changes:
    - config/database.yaml: pool_size: 10 -> pool_size: 5
    - Commit message: "Reduce connection pool for cost savings"
"""


# =============================================================================
# STATE DEFINITION
# =============================================================================

class InvestigationState(TypedDict):
    """State that flows through the harness."""
    ticket: str
    messages: Annotated[List[str], operator.add]
    hypotheses: List[str]
    findings: List[str]
    tool_outputs: Annotated[List[str], operator.add]
    confidence: float
    resolution: str
    iteration: int
    max_iterations: int


# =============================================================================
# MOCK TOOLS
# =============================================================================

def query_datadog(query: str) -> str:
    """Mock Datadog log query."""
    return MOCK_DATADOG_LOGS


def query_github(query: str) -> str:
    """Mock GitHub deployment query."""
    return MOCK_GITHUB_DEPLOYMENTS


def check_metrics(service: str) -> str:
    """Mock metrics check."""
    return f"Service {service}: CPU 45%, Memory 78%, Connections 98/100 (near limit)"


# =============================================================================
# HARNESS NODES
# =============================================================================

def think_node(state: InvestigationState) -> InvestigationState:
    """THINK: Form hypotheses and plan next actions."""
    print(f"\n🧠 THINK: Analyzing current state...")
    
    iteration = state.get("iteration", 0)
    findings = state.get("findings", [])
    
    if iteration == 0:
        hypotheses = [
            "Could be related to recent deployment",
            "Possible database connectivity issue",
            "Potential resource exhaustion",
        ]
        print(f"   Formed {len(hypotheses)} initial hypotheses")
    elif iteration == 1:
        hypotheses = ["Correlating deployment timeline with error spike"]
        print(f"   Refining hypothesis based on log analysis")
    else:
        hypotheses = ["Validating root cause"]
        print(f"   Converging on root cause")
    
    return {
        **state,
        "hypotheses": hypotheses,
        "messages": [f"THINK (iter {iteration}): Formed hypotheses"],
    }


def act_node(state: InvestigationState) -> InvestigationState:
    """ACT: Execute tools to gather evidence."""
    print(f"\n⚡ ACT: Executing investigation tools...")
    
    iteration = state.get("iteration", 0)
    outputs = []
    
    if iteration == 0:
        # First iteration: Query logs
        print("   Querying Datadog for recent 502 errors...")
        result = query_datadog("status:502 last:1h")
        outputs.append(f"Datadog: {result[:100]}...")
        
    elif iteration == 1:
        # Second iteration: Check deployments
        print("   Checking GitHub deployments...")
        result = query_github("deployments last:2h")
        outputs.append(f"GitHub: {result[:100]}...")
        
    else:
        # Third iteration: Check metrics
        print("   Checking service metrics...")
        result = check_metrics("api-gateway")
        outputs.append(f"Metrics: {result}")
    
    return {
        **state,
        "tool_outputs": outputs,
        "messages": [f"ACT (iter {iteration}): Executed tools"],
    }


def observe_node(state: InvestigationState) -> InvestigationState:
    """OBSERVE: Analyze tool outputs and extract findings."""
    print(f"\n👁️  OBSERVE: Analyzing results...")
    
    iteration = state.get("iteration", 0)
    findings = state.get("findings", [])
    
    if iteration == 0:
        finding = "Found 47 502 errors in last hour, spike at 14:21 UTC"
        print(f"   {finding}")
        findings.append(finding)
        
    elif iteration == 1:
        finding = "Deployment at 14:20 UTC changed connection pool from 10 to 5"
        print(f"   {finding}")
        findings.append(finding)
        
    else:
        finding = "Connection pool at 98% utilization, near exhaustion"
        print(f"   {finding}")
        findings.append(finding)
    
    return {
        **state,
        "findings": findings,
        "messages": [f"OBSERVE (iter {iteration}): Extracted findings"],
    }


def evaluate_node(state: InvestigationState) -> InvestigationState:
    """EVALUATE: Determine confidence and decide next action."""
    print(f"\n✅ EVALUATE: Assessing confidence...")
    
    iteration = state.get("iteration", 0)
    findings = state.get("findings", [])
    
    # Calculate confidence based on findings
    if len(findings) >= 3:
        confidence = 94.0
        resolution = (
            "Root Cause: Connection pool misconfiguration in deployment abc123\n"
            "   The pool_size was reduced from 10 to 5, causing connection exhaustion.\n"
            "   Recommended Fix: Rollback deployment or increase pool_size to 50\n"
        )
    elif len(findings) >= 2:
        confidence = 75.0
        resolution = "Partial: Deployment correlated with errors, investigating further"
    else:
        confidence = 40.0
        resolution = "Insufficient evidence, continuing investigation"
    
    # Determine action based on confidence
    if confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
        action = "AUTO-EXECUTE"
    elif confidence >= CONFIDENCE_THRESHOLDS["execute_review"]:
        action = "EXECUTE WITH REVIEW"
    elif confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
        action = "REQUIRE APPROVAL"
    else:
        action = "CONTINUE INVESTIGATION"
    
    print(f"   Confidence: {confidence}%")
    print(f"   Action: {action}")
    
    return {
        **state,
        "confidence": confidence,
        "resolution": resolution,
        "iteration": iteration + 1,
        "messages": [f"EVALUATE: Confidence {confidence}%, action: {action}"],
    }


def should_continue(state: InvestigationState) -> Literal["think", "end"]:
    """Decide whether to continue the investigation loop."""
    confidence = state.get("confidence", 0)
    iteration = state.get("iteration", 0)
    max_iterations = state.get("max_iterations", 5)
    
    # Stop if we have high confidence or hit iteration limit
    if confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
        return "end"
    if iteration >= max_iterations:
        return "end"
    
    return "think"


# =============================================================================
# BUILD THE GRAPH
# =============================================================================

def build_harness_graph():
    """Build the HACI harness investigation graph."""
    
    graph = StateGraph(InvestigationState)
    
    # Add nodes
    graph.add_node("think", think_node)
    graph.add_node("act", act_node)
    graph.add_node("observe", observe_node)
    graph.add_node("evaluate", evaluate_node)
    
    # Add edges for the harness loop
    graph.add_edge(START, "think")
    graph.add_edge("think", "act")
    graph.add_edge("act", "observe")
    graph.add_edge("observe", "evaluate")
    
    # Conditional edge to continue or end
    graph.add_conditional_edges(
        "evaluate",
        should_continue,
        {
            "think": "think",
            "end": END,
        }
    )
    
    return graph.compile()


# =============================================================================
# MAIN DEMO
# =============================================================================

def run_demo():
    """Run the HACI quick start demo."""
    
    print("=" * 60)
    print("  HACI Quick Start Demo")
    print("  Harness-Enhanced Agentic Collaborative Intelligence")
    print("=" * 60)
    
    # Check for API key
    if not os.environ.get("ANTHROPIC_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
        print("\n⚠️  Warning: No API key found.")
        print("   Set ANTHROPIC_API_KEY or OPENAI_API_KEY for full LLM integration.")
        print("   Running with mock responses for demonstration.\n")
    
    # Build the harness
    harness = build_harness_graph()
    
    # Sample ticket
    ticket = "API returning 502 errors intermittently for /api/users endpoint"
    
    print(f"\n🎯 Submitting ticket: {ticket}")
    print("-" * 60)
    
    # Initial state
    initial_state: InvestigationState = {
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
    
    # Run the investigation
    final_state = harness.invoke(initial_state)
    
    # Print results
    print("\n" + "=" * 60)
    print("  📋 INVESTIGATION COMPLETE")
    print("=" * 60)
    
    print(f"\n🔍 Findings ({len(final_state['findings'])}):")
    for i, finding in enumerate(final_state["findings"], 1):
        print(f"   {i}. {finding}")
    
    print(f"\n📊 Confidence: {final_state['confidence']}%")
    
    # Show action based on confidence
    confidence = final_state["confidence"]
    if confidence >= CONFIDENCE_THRESHOLDS["auto_execute"]:
        action_color = "🟢"
        action = "AUTO-EXECUTE"
    elif confidence >= CONFIDENCE_THRESHOLDS["execute_review"]:
        action_color = "🟡"
        action = "EXECUTE WITH POST-REVIEW"
    elif confidence >= CONFIDENCE_THRESHOLDS["require_approval"]:
        action_color = "🟠"
        action = "REQUIRE HUMAN APPROVAL"
    else:
        action_color = "🔴"
        action = "ESCALATE TO HUMAN"
    
    print(f"   {action_color} Action: {action}")
    
    print(f"\n💡 Resolution:")
    print(f"   {final_state['resolution']}")
    
    print("\n" + "=" * 60)
    print("  ✅ Demo Complete!")
    print("  See README.md for next steps to explore full HACI.")
    print("=" * 60)


if __name__ == "__main__":
    run_demo()
