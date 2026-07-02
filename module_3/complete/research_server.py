"""
research_server.py — Module 3 (Simplified) — bundled tool server
Google ADK — Core Concepts

WHAT THIS FILE IS
    An MCP (Model Context Protocol) *server*. A server's whole job is to expose
    "tools" — functions that an AI agent can call. Here we expose two research
    tools: one that searches Wikipedia and one that searches arXiv.

WHY MCP AT ALL
    Without MCP, you'd hard-code tool functions inside the agent. With MCP, the
    tools live in a separate program (this file). Any agent that speaks MCP can
    connect and use them — Claude, Google ADK, someone else's app — without
    copying your code. Write the tool once, use it anywhere.

THE ONE BIG IDEA
    The @mcp.tool() decorator is the only thing that turns an ordinary Python
    function into an MCP tool. FastMCP automatically reads:
      - the function NAME        -> becomes the tool's name
      - the function DOCSTRING   -> becomes the tool's description (what the AI
                                    reads to decide whether/when to call it)
      - the function SIGNATURE   -> becomes the input schema (arg names + types)
    So writing a clear docstring is not optional polish — it's how the model
    knows what the tool is for.

This file is fully self-contained — it does not depend on any other module.

HOW TO RUN
    python research_server.py
    (It will sit silently, waiting for a client to connect. That is correct.)

REQUIREMENTS
    pip install mcp
"""

# --- Standard-library imports -------------------------------------------------
# We use only Python's built-in modules for the HTTP calls, so there are no
# extra dependencies to install for the tool logic itself.
import json                          # parse the JSON that Wikipedia returns
import urllib.request                # make HTTP GET requests
import urllib.parse                  # safely build query strings (?a=1&b=2)
import xml.etree.ElementTree as ET   # parse the XML (Atom) feed arXiv returns

# --- The MCP framework --------------------------------------------------------
# FastMCP is the high-level helper that does all the protocol plumbing for us.
from mcp.server.fastmcp import FastMCP

# Create the server object. The string is just a human-readable server name;
# it shows up in logs and in the client when it connects.
mcp = FastMCP("research-tools")


# =============================================================================
# TOOL 1: Wikipedia search
# =============================================================================
@mcp.tool()  # <-- this decorator registers the function below as an MCP tool
def search_wikipedia(query: str) -> str:
    """
    Search Wikipedia for general background on a topic, person, place, or
    concept. Good for established facts and definitions. Not useful for very
    recent events or cutting-edge research.
    """
    # Build the request URL. urlencode turns the dict into a proper query
    # string and escapes special characters (spaces, &, etc.) for us.
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",   # we want to run a query
        "list": "search",    # specifically, a search
        "srsearch": query,   # the user's search text
        "format": "json",    # ask for JSON back (easy to parse)
        "srlimit": 3,        # cap results at 3 so the output stays short
    })

    # Wikipedia asks every caller to identify itself with a User-Agent header.
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchCompanion/1.0"})

    # Network calls can fail (no internet, timeout, rate limit). We catch any
    # error and RETURN it as a normal string instead of crashing — the agent
    # can then read that message and react, rather than the whole program dying.
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())   # bytes -> Python dict
    except Exception as exc:
        return f"Wikipedia search failed: {exc}"

    # Dig into the response structure to get the list of search hits.
    # .get(..., {}) / .get(..., []) return safe defaults if a key is missing.
    results = data.get("query", {}).get("search", [])
    if not results:
        return f"No Wikipedia results found for '{query}'."

    # Format each hit as a bullet line. The snippet contains HTML highlight
    # markup (<span class="searchmatch">...</span>) that we strip out so the
    # text is clean for the model to read.
    lines = []
    for r in results:
        snippet = r["snippet"].replace('<span class="searchmatch">', "").replace("</span>", "")
        lines.append(f"- {r['title']}: {snippet}")

    # A tool must return a single string. We join the bullet lines with newlines.
    return "\n".join(lines)


# =============================================================================
# TOOL 2: arXiv search
# =============================================================================
@mcp.tool()
def search_arxiv(query: str) -> str:
    """
    Search arXiv for academic papers. Good for cutting-edge research, technical
    methods, and citations to specific papers. Not useful for general background
    or non-technical topics.
    """
    # arXiv's API is a plain GET request too. "all:" means "search all fields".
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": 3,
    })

    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read()   # arXiv returns XML, so keep the raw bytes
    except Exception as exc:
        return f"arXiv search failed: {exc}"

    # arXiv returns an Atom XML feed. Atom tags are namespaced, so we define the
    # namespace once and pass it to every find/findall call.
    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)                    # parse XML text into a tree
    entries = root.findall("atom:entry", ns)     # each <entry> is one paper
    if not entries:
        return f"No arXiv results found for '{query}'."

    # Pull the title, author names, and a trimmed abstract from each entry.
    lines = []
    for e in entries:
        title = e.find("atom:title", ns).text.strip().replace("\n", " ")
        authors = [a.find("atom:name", ns).text for a in e.findall("atom:author", ns)]
        summary = e.find("atom:summary", ns).text.strip().replace("\n", " ")[:200]  # first 200 chars
        lines.append(f"- {title} ({', '.join(authors)}): {summary}...")
    return "\n".join(lines)


# =============================================================================
# ENTRY POINT
# =============================================================================
# This block runs only when the file is executed directly (python research_server.py),
# not when it is imported by another file.
if __name__ == "__main__":
    # mcp.run() starts the server using "stdio transport" — it talks to clients
    # over standard input/output. There is NO web page and NO port number; the
    # process just waits quietly for a client to send it MCP messages.
    # Seeing nothing printed is the expected, healthy state. Stop it with Ctrl-C.
    mcp.run()
