"""
finder_agent/agent.py — Module 4 (Simplified), Segment 1  [STUDENT STARTER]
The Finder — a retrieval specialist

The _mcp() factory and the Finder's prompt are provided. Your job: declare the
agent and give it its tool. 2 small TODOs.
Answer key: ../../finder_agent/agent.py

Run from the starter/ folder:  adk web   (pick "finder")
"""

import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

RESEARCH_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../research_server.py")
)


def _mcp(server_path: str) -> McpToolset:
    """Create a FRESH McpToolset (its own subprocess) for a server script.
    Each agent that needs the server calls this separately."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable, args=[server_path],
            )
        )
    )


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

If a source returns nothing, write "No results found." for that section.\
"""


root_agent = LlmAgent(
    name="finder",
    model="gemini-2.5-flash",
    description=(
        "Retrieves information from Wikipedia and arXiv on any research topic. "
        "Returns a structured report with one section per source. "
        "Use this agent FIRST when researching any question."
    ),
    # TODO 1: give the agent its instruction — use FINDER_PROMPT.
    instruction=None,       # <-- replace None with FINDER_PROMPT
    # TODO 2: give the agent one MCP toolset for the research server.
    #         Call the factory: _mcp(RESEARCH_SERVER_PATH), inside a list.
    tools=[],               # <-- put _mcp(RESEARCH_SERVER_PATH) in this list
)
