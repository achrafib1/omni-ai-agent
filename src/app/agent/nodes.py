# src/app/agent/nodes.py
"""
LangGraph Nodes for Omni-AI-Agent.

Implements the deterministic multi-stage cognitive architecture:
1. Memory Extraction (Does this message contain a fact?)
2. Routing (Is this chat, image, or audio?)
3. Context Injection (What is the system doing right now?)
4. Memory Injection (What relevant facts do we know about this user?)
5. Conversation Generation (Real-time token streaming to the user)
6. Summarization (Compresses old context to prevent token limits)

All nodes reach out across the network via `MCPNetworkClient` to function,
maintaining a true microservice decoupling.
"""

from typing import Dict, Any, cast

from langchain_core.messages import AIMessage, SystemMessage, HumanMessage, RemoveMessage
from langgraph.config import get_stream_writer
from pydantic import BaseModel, Field

from src.app.agent.state import OmniAgentState
from src.app.agent.utils.llm_factory import get_fast_routing_model, get_core_reasoning_model
from src.app.agent.mcp_client import MCPNetworkClient
from src.shared.domain.schemas.agent import RouterResponse
from src.shared.infrastructure.observability.logger import get_logger

logger = get_logger(__name__)

# Initialize our Network Client to point to our FastMCP Microservice
mcp_client = MCPNetworkClient("http://localhost:8001/mcp")


class MemoryExtractionResponse(BaseModel):
    """Pydantic schema enforcing strict JSON output from the extraction model."""
    is_important: bool = Field(description="True if the message contains a personal fact to remember.")
    formatted_memory: str = Field(default="", description="The isolated fact formatted in third person.")


async def memory_extraction_node(state: OmniAgentState) -> Dict[str, Any]:
    """
    Evaluates the user's message and requests the remote MCP server to store facts.
    """
    logger.info("[info]Node: Memory Extraction...[/info]")
    
    messages = state.get("messages", [])
    if not messages:
        return {}
        
    last_message = messages[-1].content
    user_id = state.get("user_id")

    # Use a high-speed, low-parameter model for rapid background classification
    # extraction_llm = get_fast_routing_model(temperature=0.1).with_structured_output(MemoryExtractionResponse)
    
    extraction_llm = get_core_reasoning_model(temperature=0.1).with_structured_output(MemoryExtractionResponse)

    prompt = (
        "Extract personal facts from the user's message. "
        "Ignore greetings or general chat. Output clearly in third person.\n"
        f"Message: '{last_message}'"
    )
    
    try:
        analysis = cast(MemoryExtractionResponse, await extraction_llm.ainvoke([HumanMessage(content=prompt)]))
        if analysis.is_important and analysis.formatted_memory:
            logger.info(f"Fact detected: '{analysis.formatted_memory}'. Dispatching to MCP Network...")
            
            # Execute database write completely decoupled over the network
            await mcp_client.execute_tool(
                tool_name="store_user_memory", 
                arguments={"user_id": user_id, "fact": analysis.formatted_memory}
            )
    except Exception as e:
        logger.warning(f"Memory extraction skipped due to error: {e}")
        
    return {}


async def router_node(state: OmniAgentState) -> Dict[str, Any]:
    """
    Determines the appropriate workflow using Opik prompts fetched via MCP.
    Returns a strict string literal to dictate the next Graph Edge.
    """
    logger.info("[info]Node: Executing Router...[/info]")
    
    # router_llm = get_fast_routing_model(temperature=0.0).with_structured_output(RouterResponse)
    
    router_llm = get_core_reasoning_model(temperature=0.0).with_structured_output(RouterResponse)


    # Fetch prompt over MCP network
    routing_prompt = await mcp_client.fetch_prompt("get_routing_system_prompt")
    if not routing_prompt:
        routing_prompt = "You are a router. Output 'conversation'."
        
    # We only analyze the last 3 messages to keep routing fast and contextual
    messages_to_analyze = list(state.get("messages", []))[-3:]
    
    try:
        response = cast(RouterResponse, await router_llm.ainvoke([SystemMessage(content=routing_prompt), *messages_to_analyze]))
        workflow = response.response_type.value
        logger.debug(f"Router successfully resolved path: [warning]{workflow}[/warning]")
        return {"current_workflow": workflow}
    except Exception as e:
        logger.error(f"[danger]Router Node failed:[/danger] {e}", exc_info=True)
        return {"current_workflow": "conversation"}


async def context_injection_node(state: OmniAgentState) -> Dict[str, Any]:
    """Requests current temporal/system activity context from the remote MCP Server."""
    logger.info("[info]Node: Injecting System Context...[/info]")
    
    # Fetch current activity over MCP network
    current_activity = await mcp_client.execute_tool("get_current_system_activity")
    logger.debug(f"Injected Temporal Activity: {current_activity}")
    
    return {"omni_activity": current_activity}


async def memory_injection_node(state: OmniAgentState) -> Dict[str, Any]:
    """Retrieves long-term memories via pgvector RAG from the remote MCP Server."""
    logger.info("[info]Node: Injecting Long-Term Semantic Memory...[/info]")
    
    user_id = state.get("user_id")
    latest_query = state.get("messages", [])[-1].content if state.get("messages") else ""
    
    # Fetch relevant memories over MCP network
    memories = await mcp_client.execute_tool(
        tool_name="retrieve_user_memories", 
        arguments={"user_id": user_id, "query": latest_query}
    )
    
    return {"memory_context": memories}


async def conversation_node(state: OmniAgentState) -> Dict[str, Any]:
    """
    Generates the final response using real-time token streaming.
    Hydrates the prompt using context gathered from previous nodes.
    """
    logger.info("[info]Node: Generating Conversation Response...[/info]")
    
    core_llm = get_core_reasoning_model(temperature=0.7)
    
    # Fetch dynamic prompt via MCP network, passing args to hydrate it remotely
    persona_prompt = await mcp_client.fetch_prompt(
        prompt_name="get_omni_character_card", 
        arguments={
            "memory_context": state.get("memory_context", ""),
            "current_activity": state.get("omni_activity", "")
        }
    )
    
    system_message = SystemMessage(content=persona_prompt)
    messages = [system_message, *state.get("messages", [])]
    
    try:
        writer = get_stream_writer()
        response_content = ""
        
        # Real-time token streaming to the active WebSocket
        async for chunk in core_llm.astream(messages):
            content = chunk.content
            if content:
                # Handle cases where chunk.content is a structured list instead of a string
                if isinstance(content, list):
                    text = "".join(item.get("text", "") if isinstance(item, dict) else str(item) for item in content)
                else:
                    text = str(content)
                
                if text:
                    response_content += text
                    writer(text)
        
        # Fallback if streaming returned empty
        if not response_content:
            response = cast(AIMessage, await core_llm.ainvoke(messages))
            return {"messages": [response]}
            
        final_response = AIMessage(content=response_content)
        logger.debug("Conversation response generated and streamed successfully.")
        return {"messages": [final_response]}
        
    except Exception as e:
        logger.error(f"[danger]Conversation Generation failed:[/danger] {e}", exc_info=True)
        return {"messages": [AIMessage(content="I am experiencing a cognitive delay.")]}


async def image_node(state: OmniAgentState) -> Dict[str, Any]:
    """Placeholder for future Image Generation implementations."""
    logger.info("[info]Node: Preparing Image Generation Response...[/info]")
    return {"messages": [AIMessage(content="Executing image synthesis routines...")]}


async def audio_node(state: OmniAgentState) -> Dict[str, Any]:
    """Placeholder for future Audio TTS/STT implementations."""
    logger.info("[info]Node: Preparing Audio Generation Response...[/info]")
    return {"messages": [AIMessage(content="Initializing dynamic speech patterns...")]}


async def summarize_node(state: OmniAgentState) -> Dict[str, Any]:
    """
    Compresses the conversation history to protect the Context Window.
    Called automatically by the routing edge if the message list grows too large.
    Returns `RemoveMessage` objects to selectively prune the LangGraph state.
    """
    logger.info("[info]Node: Summarizing Conversation History...[/info]")
    
    # Use the faster routing model for background summarization
    # summarizer_llm = get_fast_routing_model(temperature=0.3)
    
    summarizer_llm = get_core_reasoning_model(temperature=0.3)

    existing_summary = state.get("summary", "")
    
    messages = list(state.get("messages", []))
    
    prompt = (
        f"This is the existing summary: {existing_summary}\n\n"
        "Extend the summary by taking into account the following new messages. "
        "Keep it highly concise and retain core facts."
    )
    
    # We summarize everything EXCEPT the last 5 messages, ensuring the LLM 
    # maintains immediate short-term context while compressing older history.
    summary_request = [HumanMessage(content=prompt), *messages[:-5]] 
    
    try:
        response = await summarizer_llm.ainvoke(summary_request)
        new_summary = str(response.content)
        
        # Safely extract IDs to guarantee string typing (ignoring potential Null values)
        # RemoveMessage instructs LangGraph to delete these specific message IDs from state
        delete_messages = [RemoveMessage(id=m.id) for m in messages[:-5] if m.id is not None]
        
        logger.debug("Summary created and old messages successfully marked for deletion.")
        return {"summary": new_summary, "messages": delete_messages}
        
    except Exception as e:
        logger.error(f"[danger]Summarization failed:[/danger] {e}", exc_info=True)
        return {}