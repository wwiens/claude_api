"""
research_companion.py — Module 2 (Simplified), Segment 3 capstone  [STUDENT STARTER]
A self-contained MCP-backed research assistant CLI

Most of this is assembled for you from Segment 2. Two TODOs remain: loading the
tools when the connection opens, and calling a tool inside the loop.
Answer key: ../research_companion.py

Run:
    python research_companion.py
    python research_companion.py --query "What is RAG?"
"""

import argparse
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
    "Keep answers concise and well-organized."
)


def mcp_tool_to_anthropic(tool) -> dict:
    return {"name": tool.name, "description": tool.description or "", "input_schema": tool.inputSchema}


class ResearchCompanion:
    """Use as an async context manager:
        async with ResearchCompanion() as c:
            print(await c.ask("What is RAG?"))"""

    def __init__(self, verbose=True, max_iterations=5):
        self.verbose = verbose
        self.max_iterations = max_iterations
        self.messages = []
        self.tools = []
        self._client = Anthropic()
        self._stdio_cm = None
        self._session_cm = None
        self._session = None

    async def __aenter__(self):
        params = StdioServerParameters(command=sys.executable, args=[SERVER])
        self._stdio_cm = stdio_client(params)
        read, write = await self._stdio_cm.__aenter__()
        self._session_cm = ClientSession(read, write)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()

        # TODO 1: discover the server's tools and store them in Claude's format.
        #   listed = await self._session.list_tools()
        #   self.tools = [mcp_tool_to_anthropic(t) for t in listed.tools]

        if self.verbose:
            print(f"[MCP] connected. Tools: {[t['name'] for t in self.tools]}")
        return self

    async def __aexit__(self, *exc):
        if self._session_cm:
            await self._session_cm.__aexit__(*exc)
        if self._stdio_cm:
            await self._stdio_cm.__aexit__(*exc)

    async def ask(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(self.max_iterations):
            response = self._client.messages.create(
                model=MODEL, max_tokens=800, system=SYSTEM_PROMPT,
                tools=self.tools, messages=self.messages,
            )

            if response.stop_reason != "tool_use":
                self.messages.append({"role": "assistant", "content": response.content})
                return response.content[0].text

            self.messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if self.verbose:
                    print(f"  [tool call] {block.name}({block.input})")
                try:
                    # TODO 2: call the tool over MCP and read its text result.
                    #   out = await self._session.call_tool(block.name, block.input)
                    #   text = out.content[0].text if out.content else "(empty result)"
                    text = "TODO: call the tool"  # replace with the two lines above
                except Exception as exc:
                    text = f"Error calling '{block.name}': {exc}"
                tool_results.append({
                    "type": "tool_result", "tool_use_id": block.id, "content": text,
                })

            self.messages.append({"role": "user", "content": tool_results})

        return "Reached max_iterations without a final answer."


async def run_cli(query=None):
    async with ResearchCompanion() as companion:
        if query:
            print(f"\nYou: {query}")
            print(f"\nCompanion: {await companion.ask(query)}")
            return
        print("Research Companion  (Module 2) — type 'quit' to stop.")
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nGoodbye.")
                break
            if user_input.lower() in {"quit", "exit"}:
                print("Goodbye.")
                break
            if not user_input:
                continue
            print(f"\nCompanion: {await companion.ask(user_input)}")


def main():
    parser = argparse.ArgumentParser(description="Research Companion — MCP-backed CLI")
    parser.add_argument("--query", "-q", help="Answer one question and exit.")
    args = parser.parse_args()
    asyncio.run(run_cli(query=args.query))


if __name__ == "__main__":
    main()
