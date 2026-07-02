"""
fact_checker_agent/agent.py — Module 4 (Simplified), Segment 1  [STUDENT STARTER]
The Fact-Checker — a verification specialist

This is the SAME skeleton as the Finder — only the job differs. The prompt is
provided. Fill in the agent's description, instruction, and tool. 3 small TODOs.
Answer key: ../../fact_checker_agent/agent.py

Run from the starter/ folder:  adk web   (pick "fact_checker")
Tip: paste a CLAIM to check (try a false one to see CONFLICTING).
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


FACT_CHECKER_PROMPT = """\
You are the Fact-Checker agent in a Research Team.

Your ONLY job is to verify claims — do not summarize, synthesize, or add new
information.

When given research findings:
1. Identify the 3-5 most important factual claims.
2. For each, search Wikipedia with search_wikipedia to check accuracy.
3. Return a verdict for each claim.

Use exactly this format per claim:

CLAIM: [the claim being checked]
VERDICT: CONFIRMED | UNCERTAIN | CONFLICTING
EVIDENCE: [one sentence explaining the verdict]\
"""


root_agent = LlmAgent(
    name="fact_checker",
    model="gemini-2.5-flash",
    # TODO 1: write a description that says when the orchestrator should use this
    #   agent (remember: "AFTER the finder"). The orchestrator ROUTES on this text.
    description="TODO: describe what this agent verifies and when to use it",
    # TODO 2: give it the FACT_CHECKER_PROMPT as its instruction.
    instruction=None,      # <-- replace None with FACT_CHECKER_PROMPT
    # TODO 3: give it ONE research-server toolset via _mcp(RESEARCH_SERVER_PATH).
    tools=[],              # <-- put _mcp(RESEARCH_SERVER_PATH) in this list
)
