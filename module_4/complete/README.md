# Module 4 (Simplified) — Multi-Agent Orchestration with ADK

Self-contained. The bundled `research_server.py` lives in this folder, so no
path reaches into any other module.

## Setup (once)

```
pip install -r requirements.txt
```

Copy the API-key template into each agent folder and add your key:

```
cp finder_agent/.env.example       finder_agent/.env
cp fact_checker_agent/.env.example fact_checker_agent/.env
cp research_team/.env.example      research_team/.env
```

## Files

- `finder_agent/` — Segment 1: retrieval specialist (Wikipedia + arXiv).
- `fact_checker_agent/` — Segment 1: verification specialist.
- `research_team/` — Segment 2: the Synthesizer with finder + fact_checker as `sub_agents`.
- `research_server.py` — the bundled MCP server shared by all agents.
- `research_team.py` — optional capstone: the team as a CLI with `--verbose` event tracing.

## Run

```
adk web                                # from THIS folder; pick finder / fact_checker / synthesizer
python research_team.py --query "What is federated learning?" --verbose   # optional CLI
```
