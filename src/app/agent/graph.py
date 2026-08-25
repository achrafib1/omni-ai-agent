# src/app/agent/graph.py
"""
LangGraph Compiler for Omni-AI-Agent.

Assembles the sequential flow of execution nodes. By separating concerns 
into distinct nodes (Extraction -> Routing -> Context -> RAG -> Generation), 
we ensure maximum observability, reliability, and modularity.
"""

from langgraph.graph import StateGraph, START, END
from langgraph.graph.state import CompiledStateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver

from src.app.agent.state import OmniAgentState
from src.app.agent.edges import route_workflow, should_summarize
from src.app.agent.nodes import (
    memory_extraction_node,
    router_node,
    context_injection_node,
    memory_injection_node,
    conversation_node,
    image_node,
    audio_node,
    summarize_node
)
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

def build_graph() -> StateGraph:
    """Defines the DAG (Directed Acyclic Graph) for the agent."""
    logger.info("Assembling the LangGraph execution layout...")
    
    workflow = StateGraph(OmniAgentState)
    
    # 1. Add Execution Nodes
    workflow.add_node("memory_extraction_node", memory_extraction_node)
    workflow.add_node("router_node", router_node)
    workflow.add_node("context_injection_node", context_injection_node)
    workflow.add_node("memory_injection_node", memory_injection_node)
    workflow.add_node("conversation_node", conversation_node)
    workflow.add_node("image_node", image_node)
    workflow.add_node("audio_node", audio_node)
    workflow.add_node("summarize_node", summarize_node)

    # 2. Define the exact, deterministic cognitive architecture
    # Phase A: Fact Extraction & Routing
    workflow.add_edge(START, "memory_extraction_node")
    workflow.add_edge("memory_extraction_node", "router_node")
    
    # Phase B: Context & Memory Hydration
    workflow.add_edge("router_node", "context_injection_node")
    workflow.add_edge("context_injection_node", "memory_injection_node")
    
    # Phase C: Workflow Diversion
    workflow.add_conditional_edges("memory_injection_node", route_workflow)
    
    # Phase D: Terminal states for Media
    workflow.add_edge("image_node", END)
    workflow.add_edge("audio_node", END)
    
    # Phase E: Text Generation & Memory Compression
    workflow.add_conditional_edges("conversation_node", should_summarize)
    workflow.add_edge("summarize_node", END)
    
    return workflow

def compile_workflow(checkpointer: BaseCheckpointSaver) -> CompiledStateGraph:
    """Compiles the defined DAG with a persistent memory checkpointer."""
    builder = build_graph()
    return builder.compile(checkpointer=checkpointer)