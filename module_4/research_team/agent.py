"""
research_team/agent.py — Module 4 (Simplified), Segment 2  [STUDENT STARTER]
The Research Team — three agents composed with sub_agents=

The finder and fact_checker below are exactly what you built in Segment 1
(provided here complete). Your job is the ONE new concept of the module: compose
them into a Synthesizer using sub_agents=. 1 TODO.
Answer key: ../../research_team/agent.py

Run from the starter/ folder:  adk web   (pick "synthesizer")
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
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable, args=[server_path],
            )
        )
    )


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


# --- Provided complete (from Segment 1) --------------------------------------
finder = LlmAgent(
    name="finder", model="gemini-2.5-flash",
    description="Retrieves from Wikipedia and arXiv. Use FIRST.",
    instruction=FINDER_PROMPT, tools=[_mcp(RESEARCH_SERVER_PATH)],
)

fact_checker = LlmAgent(
    name="fact_checker", model="gemini-2.5-flash",
    description="Verifies claims against Wikipedia. Use AFTER the finder.",
    instruction=FACT_CHECKER_PROMPT, tools=[_mcp(RESEARCH_SERVER_PATH)],
)

# --- TODO: build the orchestrator --------------------------------------------
# Declare `root_agent` as the Synthesizer. The new idea: it has NO tools= of its
# own — instead it gets sub_agents= so it can DELEGATE. Fill the blank, then
# delete this comment.
#
# root_agent = LlmAgent(
#     name="synthesizer",
#     model="gemini-2.5-flash",
#     description="Research orchestrator that coordinates finder and fact_checker.",
#     instruction=SYNTHESIZER_PROMPT,
#     sub_agents=____,        # a list containing finder and fact_checker
# )
