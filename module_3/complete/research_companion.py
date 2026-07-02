"""
research_companion.py — Module 3 (Simplified), Segment 3 capstone
ADK agent as a CLI, plus a one-line model swap (Gemini <-> Claude)

WHAT THIS FILE IS
    Segments 1-2 ran the agent inside the `adk web` UI. This file drives the
    SAME agent from the command line using ADK's Runner directly, and shows the
    headline ADK feature: change the model in ONE place and nothing else changes.

THE FOUR MOVING PARTS (all provided by ADK)
    - LlmAgent             : the agent (model + instructions + tools)
    - McpToolset           : the tools, from the bundled MCP server
    - InMemorySessionService + Runner : run the agent and remember the conversation
    - the ask() helper     : send a message, read events, return the final text

HOW TO RUN
    python research_companion.py                          # interactive REPL (Gemini)
    python research_companion.py --query "What is RAG?"   # single question

MODEL SWAP
    Default is Gemini. To use Claude instead, comment the Gemini line and
    uncomment the Claude line below. That needs `pip install litellm` and
    ANTHROPIC_API_KEY exported in the SHELL (LiteLLM reads it from the
    environment, not from .env).

REQUIREMENTS
    pip install google-adk mcp python-dotenv        (+ litellm for the Claude swap)
    GOOGLE_API_KEY in a .env file beside this script (for Gemini)
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

# load_dotenv() reads the .env file and puts GOOGLE_API_KEY into the environment.
# It must run BEFORE the google.adk imports below, because ADK reads the key at
# import time.
load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm   # noqa: F401 — used by the Claude swap line
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types                    # types.Content / types.Part message objects
from mcp import StdioServerParameters


# --- MODEL SELECTION: change this ONE line to swap models --------------------
# A model can be a plain string (Gemini) OR a LiteLlm wrapper (any other provider).
# Everything else in this file is written to not care which one is active.
MODEL = "gemini-2.5-flash"
# MODEL = LiteLlm(model="anthropic/claude-sonnet-4-6")   # <- uncomment for Claude


# Bundled server sits beside this script — self-contained, no cross-module path.
RESEARCH_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "research_server.py"
)

SYSTEM_PROMPT = """\
You are Research Companion, a personal research assistant.

When answering questions:
1. Use search_wikipedia for background and definitions.
2. Use search_arxiv for recent academic papers.
3. Synthesize both into a clear answer and cite each source.
4. If a tool returns nothing, say so and use the other source.

Keep answers focused and well-organized.\
"""


def _make_toolset() -> McpToolset:
    """Create the toolset that connects to the bundled MCP server.
    Kept as its own function so we can also close() it cleanly at the end."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[RESEARCH_SERVER_PATH],
            )
        )
    )


async def run_session(query: str = None) -> None:
    # If MODEL is a plain string it IS the name; if it's a LiteLlm object, read
    # its .model attribute. This is only used for the friendly banner text.
    model_name = MODEL if isinstance(MODEL, str) else getattr(MODEL, "model", str(MODEL))

    # 1) Build the tools and the agent.
    toolset = _make_toolset()
    agent = LlmAgent(
        name="research_companion",
        model=MODEL,                    # <-- the one place the model is chosen
        description="Research assistant with Wikipedia and arXiv tools.",
        instruction=SYSTEM_PROMPT,
        tools=[toolset],
    )

    # 2) A session stores conversation history; the Runner executes the agent.
    #    app_name must MATCH between create_session and Runner, or the runner
    #    can't find the session.
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        state={}, app_name="research_companion", user_id="user_1"
    )
    runner = Runner(
        agent=agent, app_name="research_companion", session_service=session_service
    )

    async def ask(q: str) -> str:
        """Send one message and return the agent's final text answer.
        The Runner emits a STREAM of events (tool calls, tool results, etc.);
        we wait for the one that is the final response and pull its text out."""
        # ADK wraps messages in Content/Part objects (its version of the
        # {"role": "user", "content": "..."} dict from Modules 1-2).
        content = types.Content(role="user", parts=[types.Part(text=q)])
        async for event in runner.run_async(
            session_id=session.id, user_id="user_1", new_message=content
        ):
            # Guard: only read .parts when there IS content and it's the final
            # response — some events legitimately have content=None.
            if event.content and event.is_final_response():
                return event.content.parts[0].text
        return ""

    try:
        if query:
            # One-shot mode.
            print(f"\n[model: {model_name}]\n")
            print(await ask(query))
        else:
            # Interactive REPL. Because we reuse the same `session`, the agent
            # remembers earlier turns.
            print(f"Research Companion  (model: {model_name})")
            print("Type your question, or 'quit' to exit.\n")
            while True:
                try:
                    q = input("You: ").strip()
                except (EOFError, KeyboardInterrupt):
                    print("\nGoodbye.")
                    break
                if not q:
                    continue
                if q.lower() in ("quit", "exit", "q"):
                    print("Goodbye.")
                    break
                print(f"\nAssistant: {await ask(q)}\n")
    finally:
        # ALWAYS close the toolset so the server subprocess doesn't linger as a
        # zombie process. `finally` runs even if the user hits Ctrl-C.
        try:
            await toolset.close()
        except Exception:
            pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Companion — ADK CLI")
    parser.add_argument("--query", "-q", help="Single question to answer, then exit.")
    args = parser.parse_args()
    asyncio.run(run_session(query=args.query))


if __name__ == "__main__":
    main()
