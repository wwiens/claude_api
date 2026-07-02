"""
mcp_client_demo.py — Module 2 (Simplified), Segment 2  [STUDENT STARTER]
Connecting Claude as an MCP client

The connection setup and the two discovery steps (list_tools, one manual
call_tool) are done for you. Your job is the CORE: the adapter and the tool-use
loop. 3 small TODOs, all marked. Answer key: ../mcp_client_demo.py

Run:
    python mcp_client_demo.py
Requires: pip install mcp anthropic ; export ANTHROPIC_API_KEY=...
"""

import asyncio
import os
import sys

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "claude-sonnet-4-6"
SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_server.py")

SYSTEM_PROMPT = (
    "You are Research Companion, a focused research assistant. You can search "
    "Wikipedia and arXiv. Use a tool when the question needs information you "
    "don't already know or that may be out of date. Cite your sources. "
    "Keep answers concise."
)

client = Anthropic()


def mcp_tool_to_anthropic(tool) -> dict:
    """Convert an MCP tool descriptor into the shape Claude's API expects.
    MCP calls the schema field `inputSchema`; Claude calls it `input_schema`."""
    return {
        "name": tool.name,
        "description": tool.description or "",
        # TODO 1: map MCP's `tool.inputSchema` to Claude's `input_schema` key.
        #   Add:  "input_schema": tool.inputSchema,
    }


async def main():
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER])
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Step 1 (provided): discover the server's tools.
            listed = await session.list_tools()
            print("\n=== Tools discovered ===")
            for t in listed.tools:
                print(f"  {t.name}: {t.description.strip().splitlines()[0]}")
            tools = [mcp_tool_to_anthropic(t) for t in listed.tools]

            # Step 2 (provided): call one tool by hand, no Claude.
            print("\n=== Manual call: search_wikipedia('Model Context Protocol') ===")
            result = await session.call_tool("search_wikipedia", {"query": "Model Context Protocol"})
            print(result.content[0].text if result.content else "(empty)")

            # Step 3 (you build this): the full loop.
            question = "What is retrieval-augmented generation, and is there recent research on it?"
            print(f"\n=== Full agent loop ===\nQuestion: {question}\n")
            print("Answer:\n" + await ask(session, tools, question))


async def ask(session, tools, question, max_iterations=5):
    """Run the tool-use loop: ask Claude, run any tools it requests, repeat."""
    messages = [{"role": "user", "content": question}]

    for _ in range(max_iterations):
        response = client.messages.create(
            model=MODEL, max_tokens=800, system=SYSTEM_PROMPT,
            tools=tools, messages=messages,
        )

        # TODO 2: if Claude did NOT ask for a tool, it has a final answer.
        #   Add:  if response.stop_reason != "tool_use":
        #             return response.content[0].text

        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [tool call] {block.name}({block.input})")

            # TODO 3: run the requested tool over MCP and collect the result.
            #   - call the tool:   out = await session.call_tool(block.name, block.input)
            #   - read the text:   text = out.content[0].text if out.content else "(empty result)"
            #   - append a result dict with keys: "type": "tool_result",
            #        "tool_use_id": block.id, "content": text
            pass  # replace this line with your code

        messages.append({"role": "user", "content": tool_results})

    return "Reached max_iterations without a final answer."


if __name__ == "__main__":
    asyncio.run(main())
