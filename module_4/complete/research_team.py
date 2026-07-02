"""
research_team.py — Module 4 (Simplified), optional capstone
The Research Team as a command-line program

WHAT THIS FILE IS
    The same three-agent team from research_team/agent.py, but driven from the
    command line with ADK's Runner (like Module 3's capstone) instead of the
    adk web UI. It adds a --verbose flag that prints which agent produced each
    event, so you can SEE the finder -> fact_checker -> synthesizer sequence in
    plain text.

HOW TO RUN
    python research_team.py                                  # interactive REPL
    python research_team.py --query "What is federated learning?"
    python research_team.py --query "What is federated learning?" --verbose

REQUIREMENTS
    pip install google-adk mcp python-dotenv
    GOOGLE_API_KEY in a .env file beside this script.
"""

import argparse
import asyncio
import os
import sys
import time   # used to measure how long each event takes in --verbose mode

from dotenv import load_dotenv

load_dotenv()   # load GOOGLE_API_KEY from .env before importing ADK

from google.adk.agents import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from google.genai import types
from mcp import StdioServerParameters

# Bundled server beside this script — self-contained.
RESEARCH_SERVER_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "research_server.py"
)


def _mcp() -> McpToolset:
    """Fresh McpToolset (own subprocess) — called once per agent that needs it."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[RESEARCH_SERVER_PATH],
            )
        )
    )


# Shorter prompts than the adk web version — enough to drive the same behavior.
FINDER_PROMPT = """\
You are the Finder. Your ONLY job is to retrieve information.
1. search_wikipedia for background and definitions.
2. search_arxiv for recent academic papers.
Return a report with "## Wikipedia" and "## arXiv Papers" sections.\
"""

FACT_CHECKER_PROMPT = """\
You are the Fact-Checker. Your ONLY job is to verify claims.
Identify the 3-5 key claims, search_wikipedia for each, and return for each:
CLAIM / VERDICT (CONFIRMED | UNCERTAIN | CONFLICTING) / EVIDENCE.\
"""

SYNTHESIZER_PROMPT = """\
You are the Synthesizer, orchestrating a Research Team. In order:
1. DELEGATE to the finder to retrieve information (pass it the question).
2. DELEGATE to the fact_checker to verify claims (pass the finder's report).
3. SYNTHESIZE using only CONFIRMED or UNCERTAIN information.
Never answer from your own knowledge without calling the finder first.
Format as: ## Answer / ## Sources / ## Confidence Notes.\
"""


def _make_team():
    """Build the team and return (synthesizer, all_toolsets).

    We keep the toolsets in named variables FIRST, then hand them to the agents.
    That way we can collect them into all_toolsets and close() every one at the
    end. If we created them inline inside tools=[...], we'd lose the references
    and couldn't shut the subprocesses down cleanly.
    """
    finder_tools = _mcp()    # the finder's server connection
    checker_tools = _mcp()   # a separate connection for the fact-checker

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
        instruction=SYNTHESIZER_PROMPT, sub_agents=[finder, fact_checker],   # delegates, no tools
    )
    return synthesizer, [finder_tools, checker_tools]


async def run_session(query: str = None, verbose: bool = False) -> None:
    # Build the team (and keep the toolset handles for cleanup).
    synthesizer, all_toolsets = _make_team()

    # Session + Runner: same pattern as Module 3. app_name must match on both.
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        state={}, app_name="research_team", user_id="user_1"
    )
    runner = Runner(
        agent=synthesizer, app_name="research_team", session_service=session_service
    )

    async def ask(q: str) -> str:
        content = types.Content(role="user", parts=[types.Part(text=q)])
        t0 = time.time()      # start the clock for verbose timing
        final = ""
        # The Runner streams MANY events for a multi-agent run (one agent hands
        # off to the next). We watch them all; only the last is the final answer.
        async for event in runner.run_async(
            session_id=session.id, user_id="user_1", new_message=content
        ):
            if verbose:
                # event.author = which agent emitted this event. Printing it
                # reveals the delegation order in real time.
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
        # Close all three... er, both toolset subprocesses no matter what.
        for ts in all_toolsets:
            try:
                await ts.close()
            except Exception:
                pass


def main() -> None:
    parser = argparse.ArgumentParser(description="Research Team — multi-agent CLI")
    parser.add_argument("--query", "-q", help="Single question to answer, then exit.")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Print each event and which agent produced it.")
    args = parser.parse_args()
    asyncio.run(run_session(query=args.query, verbose=args.verbose))


if __name__ == "__main__":
    main()
