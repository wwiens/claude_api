"""
fact_checker_agent/agent.py — Module 4 (Simplified), Segment 1
The Fact-Checker — a verification specialist

WHAT THIS FILE IS
    The second specialist. Notice how little differs from the Finder: same
    imports, same _mcp() factory, same LlmAgent shape. Only the PROMPT and the
    DESCRIPTION change. That's the lesson — specialist agents are mostly the same
    code with different instructions.

ITS JOB
    Take some research findings, pull out the key factual claims, and check each
    one against Wikipedia, returning a verdict (CONFIRMED / UNCERTAIN /
    CONFLICTING). It must NOT add new information or soften the verdicts.

HOW TO RUN
    From the module4-handson-simple/ folder:
        adk web        (pick "fact_checker")
    Tip: paste a CLAIM to check, not a research question. Try a deliberately
    false claim to watch it return CONFLICTING.
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
    """Fresh McpToolset per agent (see the note in finder_agent/agent.py)."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[server_path],
            )
        )
    )


# The prompt forces a fixed, machine-readable verdict format. The Synthesizer
# later keys off the words CONFIRMED / UNCERTAIN / CONFLICTING, so the format
# matters as much as the content.
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
EVIDENCE: [one sentence explaining the verdict]

Be critical and specific. Your verdicts decide what the Synthesizer includes.\
"""


root_agent = LlmAgent(
    name="fact_checker",
    model="gemini-2.5-flash",
    # "Use AFTER the finder" tells the orchestrator this agent is second in line.
    description=(
        "Verifies the accuracy of key claims in a research report against "
        "Wikipedia. Returns CONFIRMED, UNCERTAIN, or CONFLICTING for each claim. "
        "Use this agent AFTER the finder has retrieved information."
    ),
    instruction=FACT_CHECKER_PROMPT,
    tools=[_mcp(RESEARCH_SERVER_PATH)],   # only needs Wikipedia search
)
