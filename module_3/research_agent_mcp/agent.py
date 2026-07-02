"""
research_agent_mcp/agent.py — Module 3 (Simplified), Segment 2  [STUDENT STARTER]
The same agent, but tools come from the MCP server

This is Segment 1's agent with ONE change: instead of inline functions, the
tools come from the bundled research_server.py via an McpToolset. Your job is to
finish that McpToolset. 2 small TODOs.
Answer key: ../../research_agent_mcp/agent.py

Run from the starter/ folder:  adk web   (pick "research_agent_mcp")
"""

import os
import sys

from google.adk.agents import LlmAgent
from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams
from mcp import StdioServerParameters

# Absolute path to the bundled server one level up in this same folder.
RESEARCH_SERVER_PATH = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "../research_server.py")
)

SYSTEM_PROMPT = """\
You are Research Companion, a personal research assistant.

When answering questions:
1. Use search_wikipedia for background information and definitions.
2. Use search_arxiv for recent academic papers on the topic.
3. Synthesize both sources into a clear, well-structured answer.
4. Always cite which source each piece of information came from.
5. If a tool returns no results, say so and rely on the other source.

Keep answers focused and well-organized.\
"""


root_agent = LlmAgent(
    name="research_agent_mcp",
    model="gemini-2.5-flash",
    description="Research assistant whose tools come from a local MCP server.",
    instruction=SYSTEM_PROMPT,
    tools=[
        McpToolset(
            connection_params=StdioConnectionParams(
                server_params=StdioServerParameters(
                    # TODO 1: which Python should launch the server?
                    #   command=sys.executable
                    command=None,   # <-- replace None with sys.executable
                    # TODO 2: what script should it run?
                    #   args=[RESEARCH_SERVER_PATH]
                    args=[],        # <-- put RESEARCH_SERVER_PATH in this list
                )
            )
        )
    ],
)
