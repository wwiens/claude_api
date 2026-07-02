# Module 2 — Student Starter

Fill in the `# TODO` gaps in each file. Everything else is already written.
The completed answer key for every file is in the parent folder
(`module2-handson-simple/`), so you can check yourself after each segment.

| Segment | File | What you write (TODOs) |
|---|---|---|
| 1 | `research_server.py` | Create the FastMCP server, add `@mcp.tool()` to each function, call `mcp.run()` (3 TODOs) |
| 2 | `mcp_client_demo.py` | The schema adapter + the tool-use loop (3 TODOs) |
| 3 | `research_companion.py` | Load tools on connect + call a tool in the loop (2 TODOs) |

Setup:
```
pip install mcp anthropic
export ANTHROPIC_API_KEY="sk-ant-..."
```
Run from inside this `starter/` folder (the scripts start `research_server.py`
for you):
```
python mcp_client_demo.py
python research_companion.py --query "What is RAG?"
```
