"""
research_agent/agent.py — Module 3 (Simplified), Segment 1  [STUDENT STARTER]
A first ADK agent with plain Python tools

The two tool functions and the system prompt are provided. Your job is the one
thing that IS the framework: declare the LlmAgent. 1 TODO.
Answer key: ../../research_agent/agent.py

Run from the starter/ folder:  adk web   (pick "research_agent")
"""

import json
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

from google.adk.agents import LlmAgent


def search_wikipedia(query: str) -> str:
    """Search Wikipedia for background and definitions on a topic. Good for
    established facts. Not useful for very recent events."""
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "format": "json", "srlimit": 3,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchCompanion/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except Exception as exc:
        return f"Wikipedia search failed: {exc}"
    hits = data.get("query", {}).get("search", [])
    if not hits:
        return f"No Wikipedia results found for '{query}'."
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
            raw = resp.read()
    except Exception as exc:
        return f"arXiv search failed: {exc}"
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


# TODO: declare the agent. ADK looks for a variable named EXACTLY `root_agent`.
# Fill in the two blanks (____) below, then delete this comment.
#
# root_agent = LlmAgent(
#     name="research_agent",
#     model=____,                 # the Gemini model string: "gemini-2.5-flash"
#     description="A research assistant that searches Wikipedia and arXiv.",
#     instruction=SYSTEM_PROMPT,
#     tools=____,                 # a list of the two tool functions above
# )
