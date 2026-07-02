"""
Research Companion v1 — single agent, hardcoded tools, no framework.
Module 1 capstone. Run with: python research_companion.py
"""
import os
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from anthropic import Anthropic

os.environ["ANTHROPIC_API_KEY"] = "ssh..."


MODEL = "claude-sonnet-4-6"
client = Anthropic()


def search_wikipedia(query: str, limit: int = 3) -> str:
    """Search Wikipedia for general background on a topic."""
    url = "https://en.wikipedia.org/w/api.php?" + urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": query,
        "format": "json", "srlimit": limit,
    })
    req = urllib.request.Request(url, headers={"User-Agent": "Module1-ResearchCompanion/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read())
    results = data.get("query", {}).get("search", [])
    if not results:
        return f"No Wikipedia results found for '{query}'."
    lines = []
    for r in results:
        snippet = r["snippet"].replace('<span class="searchmatch">', "").replace("</span>", "")
        lines.append(f"- {r['title']}: {snippet}")
    return "\n".join(lines)


def search_arxiv(query: str, max_results: int = 3) -> str:
    """Search arXiv for academic papers."""
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({
        "search_query": f"all:{query}", "start": 0, "max_results": max_results,
    })
    with urllib.request.urlopen(url, timeout=10) as resp:
        raw = resp.read()
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


TOOLS = [
    {
        "name": "search_wikipedia",
        "description": "Search Wikipedia for general background on a topic, person, place, or concept. Good for established facts. Not useful for very recent events or cutting-edge research.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query."}},
            "required": ["query"],
        },
    },
    {
        "name": "search_arxiv",
        "description": "Search arXiv for academic papers. Good for cutting-edge research and technical methods. Not useful for general background.",
        "input_schema": {
            "type": "object",
            "properties": {"query": {"type": "string", "description": "The search query."}},
            "required": ["query"],
        },
    },
]

TOOL_FUNCTIONS = {"search_wikipedia": search_wikipedia, "search_arxiv": search_arxiv}


class ResearchCompanion:
    """A single-agent research assistant with hardcoded tools and persistent history."""

    def __init__(self, model: str = MODEL, max_iterations: int = 5):
        self.model = model
        self.max_iterations = max_iterations
        self.messages = []

    def ask(self, user_message: str) -> str:
        self.messages.append({"role": "user", "content": user_message})

        for _ in range(self.max_iterations):
            response = client.messages.create(
                model=self.model, max_tokens=800, tools=TOOLS, messages=self.messages,
            )

            if response.stop_reason != "tool_use":
                self.messages.append({"role": "assistant", "content": response.content})
                return response.content[0].text

            self.messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for block in response.content:
                if block.type != "tool_use":
                    continue
                print(f"  [tool call] {block.name}({block.input})")
                output = TOOL_FUNCTIONS[block.name](**block.input)
                tool_results.append({
                    "type": "tool_result", "tool_use_id": block.id, "content": output,
                })
            self.messages.append({"role": "user", "content": tool_results})

        return "Reached max_iterations without a final answer."


def main():
    print("Research Companion v1 — type 'quit' to exit.")
    companion = ResearchCompanion()
    while True:
        user_input = input("\nYou: ").strip()
        if user_input.lower() in {"quit", "exit"}:
            break
        if not user_input:
            continue
        answer = companion.ask(user_input)
        print(f"\nCompanion: {answer}")


if __name__ == "__main__":
    main()
