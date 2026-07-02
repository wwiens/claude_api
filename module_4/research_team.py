"""
research_team.py — Module 4 (Simplified), OPTIONAL capstone  [STUDENT STARTER]
The Research Team as a command-line program

Optional — only if you have time. Same team as research_team/agent.py, driven by
ADK's Runner with a --verbose flag. One TODO: compose the team with sub_agents=.
Answer key: ../research_team.py

Run:
    python research_team.py --query "What is federated learning?" --verbose
"""

import argparse
import asyncio
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv()

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

RESEARCH_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "research_server.py"
)


def _mcp() -> McpToolset:
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable, args=[RESEARCH_SERVER_PATH],
            )
        )
    )


FINDER_PROMPT = "You are the Finder. Retrieve only: search_wikipedia and search_arxiv. Return ## Wikipedia and ## arXiv Papers sections."
FACT_CHECKER_PROMPT = "You are the Fact-Checker. Verify 3-5 key claims with search_wikipedia. Return CLAIM / VERDICT / EVIDENCE."
SYNTHESIZER_PROMPT = "You are the Synthesizer. Delegate to finder, then fact_checker, then synthesize using only CONFIRMED/UNCERTAIN info. Format: ## Answer / ## Sources / ## Confidence Notes."


def _make_team():
    finder_tools = _mcp()
    checker_tools = _mcp()

    finder = LlmAgent(
        name="finder", model="gemini-2.5-flash",
        description="Retrieves from Wikipedia and arXiv. Use FIRST.",
        instruction=FINDER_PROMPT, tools=[finder_tools],
    )
    fact_checker = LlmAgent(
        name="fact_checker", model="gemini-2.5-flash",
        description="Verifies claims against Wikipedia. Use AFTER the finder.",
        instruction=FACT_CHECKER_PROMPT, tools=[checker_tools],
    )
    synthesizer = LlmAgent(
        name="synthesizer", model="gemini-2.5-flash",
        description="Orchestrates finder and fact_checker into a final answer.",
        instruction=SYNTHESIZER_PROMPT,
        # TODO: give the Synthesizer its team. Add:  sub_agents=[finder, fact_checker]
        sub_agents=[],   # <-- put finder and fact_checker in this list
    )
    return synthesizer, [finder_tools, checker_tools]


async def run_session(query: str = None, verbose: bool = False) -> None:
    synthesizer, all_toolsets = _make_team()
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        state={}, app_name="research_team", user_id="user_1"
    )
    runner = Runner(agent=synthesizer, app_name="research_team", session_service=session_service)

    async def ask(q: str) -> str:
        content = types.Content(role="user", parts=[types.Part(text=q)])
        t0 = time.time()
        final = ""
        async for event in runner.run_async(
            session_id=session.id, user_id="user_1", new_message=content
        ):
            if verbose:
                author = getattr(event, "author", "?")
                kind = "final_response" if event.is_final_response() else "event"
                print(f"  [{time.time() - t0:4.1f}s] {kind} from {author}")
            if event.content and event.is_final_response():
                final = event.content.parts[0].text
        return final

    try:
        if query:
            print(await ask(query))
        else:
            print("Research Team  (type 'quit' to exit)\n")
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
                print(f"\nTeam: {await ask(q)}\n")
    finally:
        for ts in all_toolsets:
            try:
                await ts.close()
            except Exception:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Team — multi-agent CLI")
    parser.add_argument("--query", "-q", help="Single question to answer, then exit.")
    parser.add_argument("--verbose", "-v", action="store_true", help="Print each event + its agent.")
    args = parser.parse_args()
    asyncio.run(run_session(query=args.query, verbose=args.verbose))


if __name__ == "__main__":
    main()
