"""
Research Companion v1 — Module 1 Capstone
Module 1: Claude API & Ecosystem Foundations

A single-agent research assistant built with NOTHING but the raw Claude API and
hardcoded tool definitions. No MCP, no agent framework — that's the point of this
module. Modules 2-4 will evolve this exact agent.

Tools:
  - search_wikipedia : general background, no API key required
  - search_arxiv      : academic papers, no API key required
  - fetch_url         : stretch goal — fetch and extract text from a specific URL

Run:
    python research_companion_v1.py

Requires:
    pip install anthropic
    export ANTHROPIC_API_KEY="sk-ant-..."
"""

import json
import re
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"
client = Anthropic()


# ---------------------------------------------------------------------------
# Tool implementations — plain Python functions, nothing Claude-specific here.
# ---------------------------------------------------------------------------

def search_wikipedia(query: str, limit: int = 3) -> str:
    """Search Wikipedia and return short summaries of the top results."""
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query",
        "list": "search",
        "srsearch": query,
        "format": "json",
        "srlimit": limit,
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


def search_arxiv(query: str, max_results: int = 3) -> str:
    """Search arXiv and return titles, authors, and abstract snippets."""
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}",
        "start": 0,
        "max_results": max_results,
    })
    try:
        with urllib.request.urlopen(url, timeout=10) as resp:
            raw = resp.read()
    except Exception as exc:
        return f"arXiv search failed: {exc}"

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    root = ET.fromstring(raw)
    entries = root.findall("atom:entry", ns)
    if not entries:
        return f"No arXiv results found for '{query}'."

    lines = []
    for e in entries:
        title = e.find("atom:title", ns).text.strip().replace("\n", " ")
        authors = [a.find("atom:name", ns).text for a in e.findall("atom:author", ns)]
        summary = e.find("atom:summary", ns).text.strip().replace("\n", " ")[:200]
        lines.append(f"- {title} ({', '.join(authors)}): {summary}...")
    return "\n".join(lines)


def fetch_url(url: str, max_chars: int = 2000) -> str:
    """
    Stretch-goal tool: fetch a URL and return a crude text-only extraction.

    This is intentionally simple (regex strip, not a real HTML parser) — good
    enough for a teaching example, not production-grade. A real implementation
    would use something like BeautifulSoup or trafilatura.
    """
    req = urllib.request.Request(url, headers={"User-Agent": "ResearchCompanion/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            html = resp.read().decode("utf-8", errors="ignore")
    except Exception as exc:
        return f"Failed to fetch '{url}': {exc}"

    # Strip script/style blocks, then all remaining tags. Crude but effective enough.
    text = re.sub(r"<(script|style)[^>]*>.*?</\1>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return f"Fetched '{url}' but found no readable text content."
    return text[:max_chars]


# ---------------------------------------------------------------------------
# Tool registry — the shape Claude's API expects, plus a lookup table to map
# a tool name back to the function that actually implements it.
# ---------------------------------------------------------------------------

TOOLS = [
    {
        "name": "search_wikipedia",
        "description": (
            "Search Wikipedia for general background on a topic, person, place, "
            "or concept. Good for established facts and explanations. Not useful "
            "for very recent events or cutting-edge research."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "search_arxiv",
        "description": (
            "Search arXiv for academic papers. Good for cutting-edge research, "
            "technical methods, and citations to specific papers. Not useful for "
            "general background or non-technical topics."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "The search query."}
            },
            "required": ["query"],
        },
    },
    {
        "name": "fetch_url",
        "description": (
            "Fetch the text content of a specific, known URL. Use this only when "
            "the user gives you an exact URL to look at — not for general search."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "url": {"type": "string", "description": "The exact URL to fetch."}
            },
            "required": ["url"],
        },
    },
]

TOOL_FUNCTIONS = {
    "search_wikipedia": search_wikipedia,
    "search_arxiv": search_arxiv,
    "fetch_url": fetch_url,
}

SYSTEM_PROMPT = (
    "You are Research Companion, a focused research assistant. You have tools "
    "for searching Wikipedia, searching arXiv, and fetching specific URLs. "
    "Use them when the user's question needs information you don't already know "
    "or that may be out of date. Cite which source (Wikipedia, arXiv, or a URL) "
    "your information came from. Keep answers concise and well-organized."
)


# ---------------------------------------------------------------------------
# The agent itself.
# ---------------------------------------------------------------------------

class ResearchCompanion:
    """
    A single-agent research assistant with hardcoded tools and persistent
    conversation history across multiple .ask() calls.

    This is intentionally NOT using MCP or any agent framework — Module 1's
    entire point is to see this loop work with nothing but the raw API.
    Module 2 replaces the hardcoded TOOLS/TOOL_FUNCTIONS with tools served
    over MCP; the .ask() loop below barely changes.
    """

    def __init__(self, model: str = MODEL, max_iterations: int = 5, verbose: bool = True):
        self.model = model
        self.max_iterations = max_iterations
        self.verbose = verbose
        self.messages = []

    def ask(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(self.max_iterations):
            response = client.messages.create(
                model=self.model,
                max_tokens=800,
                system=SYSTEM_PROMPT,
                tools=TOOLS,
                messages=self.messages,
            )

            if response.stop_reason != "tool_use":
                self.messages.append({"role": "assistant", "content": response.content})
                return response.content[0].text

            self.messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                if self.verbose:
                    print(f"  [tool call] {block.name}({block.input})")

                function_to_call = TOOL_FUNCTIONS.get(block.name)
                if function_to_call is None:
                    output = f"Error: no implementation registered for tool '{block.name}'."
                else:
                    try:
                        output = function_to_call(**block.input)
                    except Exception as exc:
                        output = f"Error running '{block.name}': {exc}"

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": output,
                })

            self.messages.append({"role": "user", "content": tool_results})

        return "Reached max_iterations without a final answer — check for a tool-call loop."


# ---------------------------------------------------------------------------
# CLI entry point.
# ---------------------------------------------------------------------------

def main():
    print("=" * 60)
    print("Research Companion v1")
    print("Tools: search_wikipedia, search_arxiv, fetch_url")
    print("Type 'quit' or 'exit' to stop.")
    print("=" * 60)

    companion = ResearchCompanion()

    while True:
        try:
            user_input = input("\nYou: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye.")
            break

        if user_input.lower() in {"quit", "exit"}:
            print("Goodbye.")
            break
        if not user_input:
            continue

        answer = companion.ask(user_input)
        print(f"\nCompanion: {answer}")


if __name__ == "__main__":
    main()
