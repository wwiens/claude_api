# Module 3 — Student Starter

Fill in the `# TODO` gaps. `research_server.py` is provided complete (you don't
edit the server in this module). Answer key for each file is in the parent
folder (`module3-handson-simple/`).

| Segment | File | What you write (TODOs) |
|---|---|---|
| 1 | `research_agent/agent.py` | Declare the `root_agent = LlmAgent(...)` — fill `model=` and `tools=` (1 TODO) |
| 2 | `research_agent_mcp/agent.py` | Finish the `McpToolset` — `command=` and `args=` (2 TODOs) |
| 3 | `research_companion.py` | Return the final answer from the event stream (1 TODO) |

Setup:
```
pip install -r ../requirements.txt
cp research_agent/.env.example       research_agent/.env        # add GOOGLE_API_KEY
cp research_agent_mcp/.env.example   research_agent_mcp/.env
```
Run **from inside this `starter/` folder**:
```
adk web                       # pick research_agent, then research_agent_mcp
python research_companion.py --query "What is RAG?"
```
