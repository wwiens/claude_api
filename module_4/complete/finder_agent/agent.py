"""
finder_agent/agent.py — Module 4 (Simplified), Segment 1
The Finder — a retrieval specialist

WHAT THIS FILE IS
    The first of three specialist agents that will form a team. The Finder's ONE
    job is to gather raw material — search the sources and report back what they
    say, WITHOUT drawing conclusions. We build it and test it alone here; in
    Segment 2 it becomes a sub-agent of the team.

WHY A "SPECIALIST" WITH A NARROW JOB
    A capable model, left to its own devices, wants to jump straight to an
    answer. The prompt below forbids that. Keeping the Finder to pure retrieval
    means the next agents (Fact-Checker, Synthesizer) get the specifics they need
    instead of a pre-chewed summary.

HOW TO RUN
    From the module4-handson-simple/ folder:
        adk web        (pick "finder")
"""

import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Bundled server, one level up in this same module — self-contained.
RESEARCH_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../research_server.py")
)


def _mcp(server_path: str) -> McpToolset:
    """Create a FRESH McpToolset (with its own server subprocess) for a server.

    Why a factory function instead of one shared toolset? Each McpToolset owns
    its own stdio subprocess connection. When multiple agents need the same
    server (as in Segment 2), each must call _mcp() to get its OWN connection —
    sharing a single instance across agents would cause them to collide.
    """
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[server_path],
            )
        )
    )


# The prompt hard-codes the Finder's discipline: retrieve only, and always
# return the SAME section layout so downstream agents know where to look.
FINDER_PROMPT = """\
You are the Finder agent in a Research Team.

Your ONLY job is to retrieve information — do not synthesize, editorialize, or
draw conclusions.

For every query:
1. Search Wikipedia with search_wikipedia for background, definitions, history.
2. Search arXiv with search_arxiv for recent academic papers.

Return a STRUCTURED REPORT in exactly this format:

## Wikipedia
[findings]

## arXiv Papers
[paper titles and abstract excerpts]

If a source returns nothing, write "No results found." for that section.
Be thorough — your output is the raw material for the Fact-Checker and Synthesizer.\
"""


root_agent = LlmAgent(
    name="finder",
    model="gemini-2.5-flash",
    # The description is read by OTHER agents (the Synthesizer) to decide when to
    # call this one. "Use FIRST" signals its place in the pipeline.
    description=(
        "Retrieves information from Wikipedia and arXiv on any research topic. "
        "Returns a structured report with one section per source. "
        "Use this agent FIRST when researching any question."
    ),
    instruction=FINDER_PROMPT,
    tools=[_mcp(RESEARCH_SERVER_PATH)],   # one server = the two search tools
)
