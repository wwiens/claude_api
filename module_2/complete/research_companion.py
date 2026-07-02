"""
research_companion.py — Module 2 (Simplified), Segment 3 capstone
A self-contained MCP-backed research assistant CLI

WHAT THIS FILE IS
    The demo in Segment 2 showed the pieces. This turns them into a real
    command-line chat program. Two upgrades over the demo:
      1. It STARTS THE SERVER for you (you never launch research_server.py yourself).
      2. It REMEMBERS the conversation across turns, so follow-up questions work.

THE KEY PATTERN: an async context manager
    We wrap everything in a class you use like this:
        async with ResearchCompanion() as companion:
            answer = await companion.ask("...")
    Entering the `async with` block runs __aenter__ (start server, load tools).
    Leaving it runs __aexit__ (shut the server down). It's the async twin of
    `with open("file") as f:` — setup on the way in, cleanup on the way out.

HOW TO RUN
    python research_companion.py                       # interactive chat
    python research_companion.py --query "What is RAG?"   # one question, then exit

REQUIREMENTS
    pip install mcp anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
    research_server.py must be in the same folder as this file.
"""

import argparse   # parse command-line flags like --query
import asyncio     # run the async code
import os          # build the path to the server script
import sys          # sys.executable = the current Python interpreter

from anthropic import Anthropic
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

MODEL = "claude-sonnet-4-6"

# Absolute path to research_server.py next to this file (robust to any cwd).
SERVER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "research_server.py")

SYSTEM_PROMPT = (
    "You are Research Companion, a focused research assistant. You can search "
    "Wikipedia and arXiv. Use a tool when the question needs information you "
    "don't already know or that may be out of date. Cite your sources. "
    "Keep answers concise and well-organized."
)


def mcp_tool_to_anthropic(tool) -> dict:
    """Rename MCP's `inputSchema` to Claude's `input_schema`. (Same helper as the demo.)"""
    return {
        "name": tool.name,
        "description": tool.description or "",
        "input_schema": tool.inputSchema,
    }


class ResearchCompanion:
    """MCP-backed assistant used as an async context manager.

        async with ResearchCompanion() as companion:
            print(await companion.ask("What is RAG?"))
    """

    def __init__(self, verbose=True, max_iterations=5):
        # __init__ only stores settings — it does NOT open any connection yet.
        # The connection is opened later, in __aenter__.
        self.verbose = verbose                 # print [tool call] lines?
        self.max_iterations = max_iterations   # safety cap on the loop
        self.messages = []                     # the running conversation history
        self.tools = []                         # filled in once we connect
        self._client = Anthropic()             # Claude client (reads API key from env)
        # These three hold the open connection objects so __aexit__ can close them:
        self._stdio_cm = None                  # the stdio_client context manager
        self._session_cm = None                # the ClientSession context manager
        self._session = None                    # the live MCP session we call tools on

    async def __aenter__(self):
        """Runs when you ENTER the `async with` block: start server + load tools."""
        # Describe and launch the server subprocess.
        params = StdioServerParameters(command=sys.executable, args=[SERVER])
        self._stdio_cm = stdio_client(params)
        # We open the context managers manually (calling __aenter__ ourselves)
        # instead of using `async with`, because we need them to stay open for
        # the whole lifetime of this object, not just one block.
        read, write = await self._stdio_cm.__aenter__()
        self._session_cm = ClientSession(read, write)
        self._session = await self._session_cm.__aenter__()
        await self._session.initialize()   # MCP handshake

        # Discover the server's tools and convert them to Claude's format.
        listed = await self._session.list_tools()
        self.tools = [mcp_tool_to_anthropic(t) for t in listed.tools]
        if self.verbose:
            print(f"[MCP] connected. Tools: {[t['name'] for t in self.tools]}")
        return self   # whatever we return becomes the `as companion` variable

    async def __aexit__(self, *exc):
        """Runs when you LEAVE the block (even on error): shut everything down.
        We close in reverse order of opening: session first, then the subprocess."""
        if self._session_cm:
            await self._session_cm.__aexit__(*exc)
        if self._stdio_cm:
            await self._stdio_cm.__aexit__(*exc)

    async def ask(self, user_message: str) -> str:
        """One turn of conversation. Same tool-use loop as the demo, but the
        history lives on self.messages, so it PERSISTS across calls to ask()."""
        # Add the new user message to the ongoing history (not a fresh list).
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(self.max_iterations):
            response = self._client.messages.create(
                model=MODEL,
                max_tokens=800,
                system=SYSTEM_PROMPT,
                tools=self.tools,
                messages=self.messages,   # the FULL history, so Claude has context
            )

            # No tool requested -> Claude has a final answer. Save it and return.
            if response.stop_reason != "tool_use":
                self.messages.append({"role": "assistant", "content": response.content})
                return response.content[0].text

            # Otherwise, record Claude's tool-requesting turn...
            self.messages.append({"role": "assistant", "content": response.content})

            # ...run each requested tool and collect the results.
            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if self.verbose:
                    print(f"  [tool call] {block.name}({block.input})")
                # Wrap the tool call in try/except so a single failing tool
                # produces an error message Claude can read, instead of crashing.
                try:
                    out = await self._session.call_tool(block.name, block.input)
                    text = out.content[0].text if out.content else "(empty result)"
                except Exception as exc:
                    text = f"Error calling '{block.name}': {exc}"
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,   # must match the request's id
                    "content": text,
                })

            # Feed results back and loop for another round of reasoning.
            self.messages.append({"role": "user", "content": tool_results})

        return "Reached max_iterations without a final answer."


async def run_cli(query=None):
    """Drive the companion either as a one-shot (--query) or an interactive REPL."""
    # The `async with` here is what triggers __aenter__ / __aexit__ above.
    async with ResearchCompanion() as companion:
        # One-shot mode: answer a single question and return.
        if query:
            print(f"\nYou: {query}")
            print(f"\nCompanion: {await companion.ask(query)}")
            return

        # Interactive mode: loop reading lines from the keyboard.
        print("=" * 60)
        print("Research Companion  (Module 2)")
        print("Type 'quit' or 'exit' to stop.")
        print("=" * 60)
        while True:
            try:
                user_input = input("\nYou: ").strip()
            except (EOFError, KeyboardInterrupt):
                # Ctrl-D / Ctrl-C: exit gracefully instead of dumping a traceback.
                print("\nGoodbye.")
                break
            if user_input.lower() in {"quit", "exit"}:
                print("Goodbye.")
                break
            if not user_input:
                continue   # ignore blank lines
            print(f"\nCompanion: {await companion.ask(user_input)}")


def main():
    # argparse reads command-line flags. Here we define one optional --query flag.
    parser = argparse.ArgumentParser(description="Research Companion — MCP-backed CLI")
    parser.add_argument("--query", "-q", help="Answer one question and exit.")
    args = parser.parse_args()
    # asyncio.run() is the bridge from normal (sync) code into our async code.
    asyncio.run(run_cli(query=args.query))


if __name__ == "__main__":
    main()
