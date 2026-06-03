"""Test MCP server — validates tool registration and execution."""

import json

import pytest

from server.main import (
    server,
    TOOLS,
    TOOL_HANDLERS,
    handle_list_tools,
    handle_call_tool,
    _list_challenges_impl,
)


def test_tools_registered():
    assert len(TOOLS) == 5
    names = [t.name for t in TOOLS]
    assert "generate_attack_prompts" in names
    assert "analyze_defense" in names
    assert "rag_search" in names
    assert "suggest_strategy" in names
    assert "list_challenges" in names


def test_tools_have_handlers():
    for tool in TOOLS:
        assert tool.name in TOOL_HANDLERS, f"No handler for {tool.name}"


@pytest.mark.asyncio
async def test_list_tools_handler():
    result = await handle_list_tools()
    assert len(result) == 5


@pytest.mark.asyncio
async def test_call_generate_attack_prompts():
    result = await handle_call_tool("generate_attack_prompts", {
        "target": "test-agent", "context": "a secret password", "count": 2
    })
    assert len(result) == 1
    text = result[0].text
    data = json.loads(text)
    assert data["target"] == "test-agent"
    assert len(data["variants"]) == 2


@pytest.mark.asyncio
async def test_call_analyze_defense():
    result = await handle_call_tool("analyze_defense", {
        "response_text": "I cannot do that."
    })
    text = result[0].text
    assert "blocked" in text


@pytest.mark.asyncio
async def test_call_rag_search():
    result = await handle_call_tool("rag_search", {
        "query": "injection attack", "top_k": 2
    })
    text = result[0].text
    assert "results" in text


@pytest.mark.asyncio
async def test_call_suggest_strategy():
    result = await handle_call_tool("suggest_strategy", {
        "history": "[]"
    })
    text = result[0].text
    assert "strategy" in text


@pytest.mark.asyncio
async def test_call_list_challenges():
    result = await handle_call_tool("list_challenges", {})
    text = result[0].text
    data = json.loads(text)
    assert "workflow" in data
    assert "tools_summary" in data


@pytest.mark.asyncio
async def test_call_unknown_tool():
    result = await handle_call_tool("nonexistent", {})
    text = result[0].text
    assert "error" in text.lower() or "Unknown" in text
