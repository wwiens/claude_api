# Makes this folder an ADK agent package so `adk web` can discover its
# `root_agent` (here, the Synthesizer that orchestrates the whole team).
from . import agent
