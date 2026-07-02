# Module 4 — Student Starter

Fill in the `# TODO` gaps. `research_server.py` is provided complete. Answer key
for each file is in the parent folder (`module4-handson-simple/`).

| Segment | File | What you write (TODOs) |
|---|---|---|
| 1 | `finder_agent/agent.py` | Give the Finder its `instruction=` and `tools=` (2 TODOs) |
| 1 | `fact_checker_agent/agent.py` | Its routing `description=`, `instruction=`, `tools=` (3 TODOs) |
| 2 | `research_team/agent.py` | The new concept: declare the Synthesizer with `sub_agents=` (1 TODO) |
| Optional | `research_team.py` | Add `sub_agents=` in `_make_team()` (1 TODO) |

The finder and fact_checker are already written for you again inside
`research_team/agent.py` — Segment 2 is purely about composing them.

Setup:
```
pip install -r ../requirements.txt
cp finder_agent/.env.example        finder_agent/.env         # add GOOGLE_API_KEY
cp fact_checker_agent/.env.example  fact_checker_agent/.env
cp research_team/.env.example       research_team/.env
```
Run **from inside this `starter/` folder**:
```
adk web                                  # pick finder, fact_checker, then synthesizer
python research_team.py --query "What is federated learning?" --verbose   # optional
```
