"""
research_agent_mcp/agent.py — Module 3 (Simplified), Segment 2
The same agent, but tools come from the MCP server

WHAT CHANGED FROM SEGMENT 1
    Behavior is identical. The ONLY difference is the tools= argument:
        Segment 1:  tools=[search_wikipedia, search_arxiv]     # inline functions
        Segment 2:  tools=[McpToolset(... research_server.py ...)]  # from a server
    ADK connects to the server at startup, asks it for its tool list, and wires
    those tools into the agent. The server file itself is NOT modified — this is
    the whole point of MCP: the same server works with any MCP-aware framework.

HOW TO RUN
    From the module3-handson-simple/ folder:
        adk web
    then pick "research_agent_mcp" in the dropdown.
"""

import os
import sys

from google.adk.agents import LlmAgent

# The three MCP imports. The MIDDLE one lives in a deeply nested module and is
# the one people most often forget — if you get an ImportError, check this line.
from google.adk.tools.mcp_tool import McpToolset                              # the toolset object
from google.adk.tools.mcp_tool.mcp_session_manager import StdioConnectionParams  # how ADK connects
from mcp import StdioServerParameters                                          # how to launch the server

# Build an absolute path to the bundled server ONE level up in this same module.
# `../research_server.py` keeps everything inside module3-handson-simple/ —
# nothing reaches into another module's folder (self-contained). abspath()
# makes it work regardless of which directory `adk web` was launched from.
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
        # McpToolset = "get my tools from this MCP server."
        McpToolset(
            connection_params=StdioConnectionParams(
                # StdioServerParameters says HOW to start the server: run the
                # current Python interpreter (sys.executable) on the server file.
                server_params=StdioServerParameters(
                    command=sys.executable,
                    args=[RESEARCH_SERVER_PATH],
                )
            )
        )
    ],
)
