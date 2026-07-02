# Makes this folder a package and imports agent.py so `adk web` can find the
# `root_agent` defined there. (Same role as in research_agent/__init__.py.)
from . import agent
