"""
research_companion.py — Module 3 (Simplified), Segment 3 capstone  [STUDENT STARTER]
ADK agent as a CLI, plus a one-line model swap (Gemini <-> Claude)

The Runner/session wiring is assembled for you. Your job is the heart of the ADK
event loop: pulling the final answer out of the event stream. 1 TODO.
(Optional: try the model swap at the top.)
Answer key: ../research_companion.py

Run:
    python research_companion.py --query "What is RAG?"
"""

import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm  # noqa: F401 (used by the Claude swap)
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters


# Model: leave as Gemini for now. (Optional swap: comment this line and
# uncomment the Claude line — needs `pip install litellm` and ANTHROPIC_API_KEY.)
MODEL = "gemini-2.5-flash"
# MODEL = LiteLlm(model="anthropic/claude-sonnet-4-6")

RESEARCH_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "research_server.py"
)

SYSTEM_PROMPT = """\
You are Research Companion, a personal research assistant.
Use search_wikipedia for background, search_arxiv for recent papers, cite
sources, and keep answers focused.\
"""


def _make_toolset() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable, args=[RESEARCH_SERVER_PATH],
            )
        )
    )


async def run_session(query: str = None) -> None:
    model_name = MODEL if isinstance(MODEL, str) else getattr(MODEL, "model", str(MODEL))

    toolset = _make_toolset()
    agent = LlmAgent(
        name="research_companion", model=MODEL,
        description="Research assistant with Wikipedia and arXiv tools.",
        instruction=SYSTEM_PROMPT, tools=[toolset],
    )

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        state={}, app_name="research_companion", user_id="user_1"
    )
    runner = Runner(agent=agent, app_name="research_companion", session_service=session_service)

    async def ask(q: str) -> str:
        content = types.Content(role="user", parts=[types.Part(text=q)])
        async for event in runner.run_async(
            session_id=session.id, user_id="user_1", new_message=content
        ):
            # TODO: when this event is the FINAL response, return its text.
            #   The final answer lives at:  event.content.parts[0].text
            #   Guard first so you don't read .parts on an empty event:
            #       if event.content and event.is_final_response():
            #           return event.content.parts[0].text
            pass
        return ""

    try:
        if query:
            print(f"\n[model: {model_name}]\n")
            print(await ask(query))
        else:
            print(f"Research Companion  (model: {model_name}) — type 'quit' to exit.\n")
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
