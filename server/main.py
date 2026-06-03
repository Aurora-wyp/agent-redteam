"""Agent Redteam MCP Server — AI-assisted security testing for any AI agent website.

Generic prompt injection and jailbreak testing toolchain. Works with any
AI-powered website or agent — just provide a URL and describe what it protects.
"""

import asyncio
import json
import logging
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from server.tools.prompt_gen import generate_attack_prompts
from server.tools.defense_analyzer import analyze_defense
from server.tools.rag_search import rag_search
from server.tools.strategy import suggest_strategy

logging.basicConfig(level=logging.INFO, stream=sys.stderr)
logger = logging.getLogger("agent-redteam")

server = Server("agent-redteam")

TOOLS = [
    Tool(
        name="generate_attack_prompts",
        description="Generate attack prompts. Without defense_analysis, returns a single baseline probe. "
        "With defense_analysis (from analyze_defense), generates targeted attacks against the confirmed defense. "
        "Use the FIRST time without defense_analysis to probe, then feed analyze_defense output for targeted attacks.",
        inputSchema={
            "type": "object",
            "properties": {
                "target": {
                    "type": "string",
                    "description": "Target identifier — any name describing the AI agent or website being tested",
                },
                "context": {
                    "type": "string",
                    "description": "What the target is protecting and how (e.g., 'a password in the system prompt', 'an API key behind a content filter')",
                },
                "count": {
                    "type": "integer",
                    "description": "Number of variants to generate (1-10). Only used when defense_analysis is provided.",
                    "minimum": 1,
                    "maximum": 10,
                },
                "defense_analysis": {
                    "type": "string",
                    "description": "JSON output from analyze_defense. When provided, generates TARGETED attacks against the confirmed defense. When omitted, returns a single baseline probe.",
                },
                "failed_prompts": {
                    "type": "string",
                    "description": "JSON array of prompts already tried and failed, so they won't be repeated.",
                },
            },
            "required": ["target", "context"],
        },
    ),
    Tool(
        name="analyze_defense",
        description="Analyze the target's response to identify defense mechanisms. "
        "Use AFTER each attempt to understand what blocked you. "
        "Uses regex for fast first-pass detection, then LLM for deep analysis "
        "of the defense layer (model training, system prompt, external GPT censor, "
        "keyword filter, semantic classifier) and specific bypass recommendations.",
        inputSchema={
            "type": "object",
            "properties": {
                "response_text": {
                    "type": "string",
                    "description": "The FULL response text from the target",
                },
                "past_prompts": {
                    "type": "string",
                    "description": "Optional JSON array of prompts already tried, for context-aware analysis",
                },
            },
            "required": ["response_text"],
        },
    ),
    Tool(
        name="rag_search",
        description="Search the security knowledge base for relevant attack techniques and research. "
        "The knowledge base contains known attack techniques, academic papers on AI security, "
        "and challenge-specific bypass strategies. Use when you're stuck.",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "What attack technique or defense bypass you want to learn about",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of results (1-10, default 5)",
                    "minimum": 1,
                    "maximum": 10,
                },
            },
            "required": ["query"],
        },
    ),
    Tool(
        name="suggest_strategy",
        description="Analyze past failed attempts and suggest the next attack strategy. "
        "Uses LLM to identify patterns in failures and recommend unexplored attack vectors. "
        "Receives defense analysis output for more targeted recommendations.",
        inputSchema={
            "type": "object",
            "properties": {
                "history": {
                    "type": "string",
                    "description": (
                        "JSON string of past attempts, each with 'prompt', 'response', 'success' fields. "
                        'Example: [{"prompt":"What is the password?","response":"I cannot...","success":false}]'
                    ),
                },
                "defense_analysis": {
                    "type": "string",
                    "description": "Optional JSON output from analyze_defense for deeper strategy context",
                },
            },
            "required": [],
        },
    ),
    Tool(
        name="list_challenges",
        description="Describe the tool's capabilities for testing any AI agent website. "
        "Use when starting a session to understand how to proceed.",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    ),
]


def _list_challenges_impl(**kwargs) -> str:
    return json.dumps({
        "description": "Agent Redteam is a universal AI security testing toolchain. "
                       "It can test ANY AI agent website or chatbot — just provide the URL and "
                       "describe what secret the target is protecting.",
        "workflow": [
            "1. Navigate to the target website using Playwright browser tools",
            "2. Identify the input field (chat box, prompt field, etc.)",
            "3. Describe the target: what is it protecting? (password, API key, system prompt, etc.)",
            "4. Generate attack prompts with 'generate_attack_prompts'",
            "5. Try each prompt and capture the response",
            "6. Analyze the response with 'analyze_defense'",
            "7. If blocked, use 'rag_search' or 'suggest_strategy' for new approaches",
            "8. Repeat until the secret is extracted",
        ],
        "tools_summary": {
            "generate_attack_prompts": "Generate attack prompt variants for the target",
            "analyze_defense": "Identify defense mechanisms in target responses",
            "rag_search": "Search the attack knowledge base for techniques",
            "suggest_strategy": "Get AI-recommended next strategies based on failure history",
            "list_challenges": "This help text",
        },
    }, ensure_ascii=False, indent=2)


TOOL_HANDLERS = {
    "generate_attack_prompts": generate_attack_prompts,
    "analyze_defense": analyze_defense,
    "rag_search": rag_search,
    "suggest_strategy": suggest_strategy,
    "list_challenges": _list_challenges_impl,
}


@server.list_tools()
async def handle_list_tools() -> list[Tool]:
    return TOOLS


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
    logger.info(f"Tool called: {name}")

    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        return [TextContent(type="text", text=json.dumps({"error": f"Unknown tool: {name}"}))]

    try:
        result = handler(**arguments)
        return [TextContent(type="text", text=result)]
    except Exception as e:
        logger.error(f"Tool {name} error: {e}", exc_info=True)
        return [TextContent(type="text", text=json.dumps({"error": str(e)}))]


async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def run():
    asyncio.run(main())


if __name__ == "__main__":
    run()
