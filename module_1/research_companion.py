"""
Research Companion v1 — single agent, hardcoded tools, no framework.
Module 1 capstone. Run with: python research_companion.py
"""
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from anthropic import Anthropic

MODEL = "claude-sonnet-4-6"
client = Anthropic()


def search_wikipedia(query: str, limit: int = 3) -> str:
    """Search Wikipedia for general background on a topic."""
    # TODO: Paste in your search_wikipedia implementation from above
    pass


def search_arxiv(query: str, max_results: int = 3) -> str:
    """Search arXiv for academic papers."""
    # TODO: Paste in your search_arxiv implementation from above
    pass


TOOLS = [
    # TODO: Paste in your TOOLS list from above (or Segment B)
]

TOOL_FUNCTIONS = {"search_wikipedia": search_wikipedia, "search_arxiv": search_arxiv}


class ResearchCompanion:
    """A single-agent research assistant with hardcoded tools and persistent history."""

    def __init__(self, model: str = MODEL, max_iterations: int = 5):
        # TODO: Paste in your __init__ implementation from above
        pass

    def ask(self, user_message: str) -> str:
        # TODO: Paste in your ask() implementation from above
        pass


def main():
    # TODO: Write a simple CLI loop:
    #   1. Print a welcome message, e.g. "Research Companion v1 — type 'quit' to exit."
    #   2. Create a ResearchCompanion instance
    #   3. Loop forever:
    #      a. input("\nYou: ").strip()
    #      b. If the input is "quit" or "exit", break
    #      c. If the input is empty, continue
    #      d. Call companion.ask(user_input) and print the result
    pass


if __name__ == "__main__":
    main()
