# This one line is what makes the folder an importable Python package AND what
# lets `adk web` discover the agent. When ADK scans this folder it imports the
# package, which runs this line, which imports agent.py — and agent.py defines
# the `root_agent` variable that ADK looks for. Without this file (or this line),
# the agent won't show up in the adk web dropdown.
from . import agent
