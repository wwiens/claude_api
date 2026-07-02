"""
research_team/agent.py — Module 4 (Simplified), Segment 2
The Research Team — three agents composed with sub_agents=

WHAT THIS FILE IS
    The payoff of the module: a MULTI-AGENT system. We take the Finder and
    Fact-Checker from Segment 1 and make them sub-agents of a third agent, the
    Synthesizer. The Synthesizer coordinates them and writes the final answer.

THE KEY IDEA: sub_agents=
    A normal agent has tools= (functions it can call). This Synthesizer instead
    has sub_agents= (other AGENTS it can delegate to). It has NO tools of its
    own, so it literally cannot search anything itself — it must delegate. That
    constraint is what turns it into an orchestrator rather than a doer.

WHAT'S REUSED
    The `finder` and `fact_checker` below are the exact same agents from
    Segment 1 — same names, models, prompts, tools. The only change is they're
    now local variables handed to the Synthesizer, instead of being `root_agent`.

HOW TO RUN
    From the module4-handson-simple/ folder:
        adk web        (pick "synthesizer")
    Watch the Events tab to see the Synthesizer transfer control to finder, then
    fact_checker, then write the answer.
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
    """One call = one fresh subprocess connection. Two agents both use the
    research server, so _mcp() is called twice below — each gets its OWN
    connection. Never share a single McpToolset instance across agents."""
    return McpToolset(
        connection_params=StdioConnectionParams(
            server_params=StdioServerParameters(
                command=sys.executable,
                args=[server_path],
            )
        )
    )


# --- The three agents' instructions ------------------------------------------
FINDER_PROMPT = """\
You are the Finder agent in a Research Team.

Your ONLY job is to retrieve information — do not synthesize or draw conclusions.

For every query:
1. Search Wikipedia with search_wikipedia for background and definitions.
2. Search arXiv with search_arxiv for recent academic papers.

Return a STRUCTURED REPORT in exactly this format:

## Wikipedia
[findings]

## arXiv Papers
[paper titles and abstract excerpts]

If a source returns nothing, write "No results found." for that section.\
"""

FACT_CHECKER_PROMPT = """\
You are the Fact-Checker agent in a Research Team.

Your ONLY job is to verify claims — do not summarize or add new information.

When given research findings:
1. Identify the 3-5 most important factual claims.
2. For each, search Wikipedia with search_wikipedia to check accuracy.
3. Return a verdict for each claim in exactly this format:

CLAIM: [the claim]
VERDICT: CONFIRMED | UNCERTAIN | CONFLICTING
EVIDENCE: [one sentence explaining the verdict]\
"""

# The Synthesizer's prompt is the most important one: it spells out the pipeline
# (finder -> fact_checker -> synthesize) as explicit numbered steps. Vague
# delegation instructions are the #1 reason a multi-agent system misbehaves.
SYNTHESIZER_PROMPT = """\
You are the Synthesizer — the orchestrator of a three-agent Research Team.

For every research question, follow these steps IN ORDER:

1. DELEGATE to the finder agent to retrieve information. Pass it the question.
2. DELEGATE to the fact_checker agent to verify key claims. Pass it the
   finder's complete report.
3. SYNTHESIZE the final answer using only CONFIRMED or UNCERTAIN information.
   Do not include CONFLICTING claims unless you explicitly note the conflict.

Never answer from your own knowledge without calling the finder first.

Format the final answer as:
## Answer
[clear, well-structured response]

## Sources
[Wikipedia, arXiv paper titles used]

## Confidence Notes
[any UNCERTAIN or CONFLICTING claims and why]\
"""


# --- The two specialists (identical to Segment 1, just as local variables) ----
finder = LlmAgent(
    name="finder",
    model="gemini-2.5-flash",
    description=(
        "Retrieves information from Wikipedia and arXiv on any research topic. "
        "Use this agent FIRST when researching any question."
    ),
    instruction=FINDER_PROMPT,
    tools=[_mcp(RESEARCH_SERVER_PATH)],   # its own server connection
)

fact_checker = LlmAgent(
    name="fact_checker",
    model="gemini-2.5-flash",
    description=(
        "Verifies key claims in a research report against Wikipedia. "
        "Use this agent AFTER the finder has retrieved information."
    ),
    instruction=FACT_CHECKER_PROMPT,
    tools=[_mcp(RESEARCH_SERVER_PATH)],   # a SEPARATE server connection
)

# --- The orchestrator. This is the root_agent adk web will load. --------------
root_agent = LlmAgent(
    name="synthesizer",
    model="gemini-2.5-flash",
    description=(
        "Research orchestrator that coordinates the finder and fact_checker "
        "to produce accurate, well-sourced answers."
    ),
    instruction=SYNTHESIZER_PROMPT,
    # sub_agents (not tools!) — the Synthesizer delegates to these two agents.
    sub_agents=[finder, fact_checker],
)
