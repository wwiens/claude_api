"""
research_agent/agent.py — Module 3 (Simplified), Segment 1
A first ADK agent with plain Python tools

WHAT THIS FILE IS
    Your first agent built with Google's Agent Development Kit (ADK). In Modules
    1-2 you wrote the "call a tool, feed the result back, repeat" loop by hand.
    ADK runs that loop FOR you. All you supply is: which model, what instructions,
    and which tools.

THE WHOLE FRAMEWORK IS THE OBJECT AT THE BOTTOM
    Everything above `root_agent` is just two ordinary Python tool functions.
    The agent itself is one LlmAgent(...) call. ADK reads each tool function's
    DOCSTRING as its description — the same idea as FastMCP in Module 2.

HOW TO RUN
    From the module3-handson-simple/ folder:
        adk web
    then pick "research_agent" in the browser dropdown.
"""

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

# LlmAgent is ADK's core building block: a language model + instructions + tools.
from google.adk.agents import LlmAgent


def search_wikipedia(query: str) -> str:
    """Search Wikipedia for background and definitions on a topic. Good for
    established facts. Not useful for very recent events."""
    # Build the query string, then GET the JSON search results (same logic as
    # the Module 2 server — here it's just an in-process function, no MCP).
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "format": "json", "srlimit": 3,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchCompanion/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        return f"Wikipedia search failed: {exc}"   # return errors as text, don't crash
    hits = data.get("query", {}).get("search", [])
    if not hits:
        return f"No Wikipedia results found for '{query}'."
    # Strip Wikipedia's <span> highlight markup and format as bullets.
    parts = []
    for h in hits:
        snippet = h["snippet"].replace('<span class="searchmatch">', "").replace("</span>", "")
        parts.append(f"- {h['title']}: {snippet}")
    return "\n".join(parts)


def search_arxiv(query: str) -> str:
    """Search arXiv for recent academic papers on a topic. Good for cutting-edge
    research and citations. Not useful for general background."""
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}", "start": 0, "max_results": 3,
    })
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            raw = resp.read()   # arXiv returns XML
    except Exception as exc:
        return f"arXiv search failed: {exc}"
    # Parse the Atom XML feed; each <entry> is one paper.
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = ET.fromstring(raw).findall("atom:entry", ns)
    if not entries:
        return f"No arXiv results found for '{query}'."
    parts = []
    for e in entries:
        title = e.find("atom:title", ns).text.strip().replace("\n", " ")
        summary = e.find("atom:summary", ns).text.strip().replace("\n", " ")[:200]
        parts.append(f"- {title}: {summary}...")
    return "\n".join(parts)


# The instruction (a.k.a. system prompt) tells the model its role and how to use
# the tools. ADK passes this to the model on every turn.
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


# =============================================================================
# THE AGENT. `adk web` looks for a variable named EXACTLY `root_agent`.
# =============================================================================
root_agent = LlmAgent(
    name="research_agent",                    # shows up in the adk web dropdown
    model="gemini-2.5-flash",                 # which model does the reasoning
    description="A research assistant that searches Wikipedia and arXiv.",
    instruction=SYSTEM_PROMPT,                 # the role/behavior instructions
    tools=[search_wikipedia, search_arxiv],   # just pass the functions directly
)
