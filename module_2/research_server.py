"""
research_server.py — Module 2 (Simplified), Segment 1  [STUDENT STARTER]
Building Claude Agents with MCP

Your job: turn these two plain Python functions into an MCP server.
The function BODIES are already written for you — you only add the MCP pieces.

There are 3 small TODOs, all marked below. The complete answer key is in the
parent folder (../research_server.py) if you get stuck.

Run it when done:
    python research_server.py     (it will sit silently, waiting — that's correct)
"""

import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

from mcp.server.fastmcp import FastMCP

mcp = FastMCP("research-tools")


# TODO 2: add the @mcp.tool() decorator on the line ABOVE each function below.
# That single decorator is what turns a normal function into an MCP tool —
# FastMCP reads the function name as the tool name and the docstring as the
# description Claude will see.

def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for general background on a topic, person, place, or
    concept. Good for established facts and definitions. Not useful for very
    recent events or cutting-edge research.
    """
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
    results = data.get("query", {}).get("search", [])
    if not results:
        return f"No Wikipedia results found for '{query}'."
    lines = []
    for r in results:
        snippet = r["snippet"].replace('<span class="searchmatch">', "").replace("</span>", "")
        lines.append(f"- {r['title']}: {snippet}")
    return "\n".join(lines)


def search_arxiv(query: str) -> str:
    """
    Search arXiv for academic papers. Good for cutting-edge research, technical
    methods, and citations to specific papers. Not useful for general background
    or non-technical topics.
    """
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}", "start": 0, "max_results": 3,
    })
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read()
    except Exception as exc:
        return f"arXiv search failed: {exc}"
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    entries = ET.fromstring(raw).findall("atom:entry", ns)
    if not entries:
        return f"No arXiv results found for '{query}'."
    lines = []
    for e in entries:
        title = e.find("atom:title", ns).text.strip().replace("\n", " ")
        authors = [a.find("atom:name", ns).text for a in e.findall("atom:author", ns)]
        summary = e.find("atom:summary", ns).text.strip().replace("\n", " ")[:200]
        lines.append(f"- {title} ({', '.join(authors)}): {summary}...")
    return "\n".join(lines)


if __name__ == "__main__":
    # TODO 3: start the server on stdio transport.
    #   Replace the line below with:  mcp.run()
    raise SystemExit("TODO: call mcp.run() to start the server, then delete this line.")
