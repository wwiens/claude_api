# Makes this folder an ADK agent package: importing it runs agent.py, which
# defines the `root_agent` that `adk web` looks for. Required for the agent to
# appear in the dropdown.
from . import agent
