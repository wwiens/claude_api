"""
mcp_client_demo.py — Module 2 (Simplified), Segment 2
Connecting Claude as an MCP client

WHAT THIS FILE IS
    In Segment 1 we built a *server* (research_server.py). This file is the
    *client*: the program that connects to that server, discovers its tools,
    and lets Claude use them to answer a question.

THE THREE THINGS A CLIENT DOES (this script shows each on its own)
    1. list_tools()  — connect to the server and ask "what tools do you have?"
    2. call_tool()    — run one tool by hand, WITHOUT Claude, to prove it works
    3. ask()          — the full "agentic loop": Claude decides which tools to
                        call, we run them, feed results back, and repeat until
                        Claude produces a final answer.

HOW TO RUN
    python mcp_client_demo.py
    (research_server.py must be in the same folder — this script starts it for you.)

REQUIREMENTS
    pip install mcp anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
"""

import asyncio   # MCP's client library is async, so we need asyncio to run it
import os        # to build a file path to the server script
import sys        # sys.executable = the exact Python interpreter we're running

# Anthropic SDK — the client library for talking to Claude.
from anthropic import Anthropic

# MCP client-side pieces:
#   StdioServerParameters — describes HOW to launch the server (command + args)
#   stdio_client          — actually launches it and opens a read/write channel
#   ClientSession         — speaks the MCP protocol over that channel
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

# --- Configuration ------------------------------------------------------------
MODEL = "claude-sonnet-4-6"

# Build an absolute path to research_server.py sitting next to THIS file.
# __file__ is this script's path; dirname() is its folder; join() adds the name.
# Doing it this way means the script works no matter what directory you run it from.
SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_server.py")

# The system prompt sets Claude's role and, importantly, tells it WHEN to reach
# for a tool versus answering from memory.
SYSTEM_PROMPT = (
    "You are Research Companion, a focused research assistant. You can search "
    "Wikipedia and arXiv. Use a tool when the question needs information you "
    "don't already know or that may be out of date. Cite your sources. "
    "Keep answers concise."
)

# Create the Claude client once. It reads ANTHROPIC_API_KEY from the environment
# automatically — you never paste your key into the code.
client = Anthropic()


def mcp_tool_to_anthropic(tool) -> dict:
    """Convert an MCP tool descriptor into the shape Claude's API expects.

    MCP and Claude describe tools almost identically. The ONE difference is the
    field name for the argument schema: MCP calls it `inputSchema` (camelCase),
    Claude's API calls it `input_schema` (snake_case). This function is just
    that rename plus copying name and description across.
    """
    return {
        "name": tool.name,
        "description": tool.description or "",   # "" guards against a missing description
        "input_schema": tool.inputSchema,        # <-- the only real translation
    }


async def main():
    # Describe how to start the server: run "this Python" on "research_server.py".
    server_params = StdioServerParameters(command=sys.executable, args=[SERVER])

    # `async with stdio_client(...)` launches the server as a subprocess and
    # gives us a (read, write) pair to talk to it. When the block exits, the
    # subprocess is shut down automatically. ClientSession wraps that channel in
    # the MCP protocol.
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # initialize() performs the MCP handshake. Always call it first.
            await session.initialize()

            # --- 1. DISCOVER the tools the server offers -----------------------
            # The server — not the agent — is the source of truth for the tool list.
            listed = await session.list_tools()
            print("\n=== Tools discovered from research_server.py ===")
            for t in listed.tools:
                # Print the tool name and the first line of its description.
                print(f"  {t.name}: {t.description.strip().splitlines()[0]}")

            # Convert each MCP tool into Claude's format so we can pass them to the API.
            tools = [mcp_tool_to_anthropic(t) for t in listed.tools]

            # --- 2. CALL one tool by hand, no Claude involved ------------------
            # This proves the tool works and that MCP round-trips correctly.
            print("\n=== Manual tool call: search_wikipedia('Model Context Protocol') ===")
            result = await session.call_tool(
                "search_wikipedia", {"query": "Model Context Protocol"}
            )
            # call_tool returns a result object; the text lives in .content[0].text
            print(result.content[0].text if result.content else "(empty)")

            # --- 3. THE FULL AGENT LOOP ----------------------------------------
            question = "What is retrieval-augmented generation, and is there recent research on it?"
            print(f"\n=== Full agent loop ===\nQuestion: {question}\n")
            answer = await ask(session, tools, question)
            print(f"\nAnswer:\n{answer}")


async def ask(session, tools, question, max_iterations=5):
    """Run the tool-use loop.

    The loop repeats: ask Claude -> if Claude wants tools, run them and send the
    results back -> ask again. It ends when Claude replies with a normal text
    answer instead of a tool request. `max_iterations` is a safety cap so a
    misbehaving loop can't run forever.
    """
    # `messages` is the running conversation. We start with the user's question.
    messages = [{"role": "user", "content": question}]

    for _ in range(max_iterations):
        # Send the whole conversation plus the available tools to Claude.
        response = client.messages.create(
            model=MODEL,
            max_tokens=800,
            system=SYSTEM_PROMPT,
            tools=tools,
            messages=messages,
        )

        # stop_reason tells us WHY Claude stopped. If it's not "tool_use", Claude
        # is done thinking and has given a normal answer — return it.
        if response.stop_reason != "tool_use":
            return response.content[0].text

        # Otherwise Claude wants to call one or more tools. First, record Claude's
        # turn (which contains the tool requests) in the conversation history.
        messages.append({"role": "assistant", "content": response.content})

        # A single response can request MULTIPLE tools, so we loop over every
        # block and collect a result for each one.
        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue  # skip any plain-text blocks Claude included
            print(f"  [tool call] {block.name}({block.input})")

            # Run the requested tool on the server with the arguments Claude chose.
            out = await session.call_tool(block.name, block.input)
            text = out.content[0].text if out.content else "(empty result)"

            # Each result must be tagged with the SAME tool_use_id Claude gave the
            # request, so Claude can match answer-to-question when it reads them.
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": text,
            })

        # Send all the tool results back as the next "user" turn, then loop.
        messages.append({"role": "user", "content": tool_results})

    # If we burned through max_iterations without a final answer, say so.
    return "Reached max_iterations without a final answer."


# Standard entry point. asyncio.run() starts the async main() coroutine.
if __name__ == "__main__":
    asyncio.run(main())
