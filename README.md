# MCP GitHub Operations PoC

This project provides a modular, extensible framework for automating GitHub repository, PR, CI, and documentation operations, with integration to Notion and Confluence.

## Features
- **Pull Request Tools**: Fetch, create, and merge PRs; create Notion and Confluence pages for PR analysis.
- **Repository Tools**: Create repositories, set up language templates, generate Dockerfiles and README.md files.
- **CI Tools**: Analyze GitHub Actions pipeline results and provide recommendations.
- **Test Generation**: Auto-generate Python unittest stubs for all functions/classes in the repo.

## Modular Architecture

The codebase is organized into logical modules for maintainability:

```
project-root/
  github_ops/
    auth.py         # Authentication and client setup (GitHub, Notion, Confluence)
    pr_tools.py     # Pull request tools (fetch, create, merge, Notion/Confluence pages)
    repo_tools.py   # Repository management tools (create repo, templates, Dockerfile, README)
    ci_tools.py     # CI pipeline analysis tools
    testgen.py      # Test generation tools
  pr_analyzer.py    # Main orchestration/entry point
  tests/            # Test stubs auto-generated here
  requirements.txt  # Python dependencies
  README.md         # This file
```

### Tool Registration
Each tool group is registered in `pr_analyzer.py`:
```python
from github_ops.pr_tools import register_pr_tools
from github_ops.repo_tools import register_repo_tools
from github_ops.ci_tools import register_ci_tools
from github_ops.testgen import register_testgen_tools

# ...
register_pr_tools(...)
register_repo_tools(...)
register_ci_tools(...)
register_testgen_tools(...)
```

## Extending the System
- To add new tools, create a new module in `github_ops/` or extend an existing one.
- Register new tools using the `@mcp.tool()` decorator in the appropriate module.
- Import and call the registration function in `pr_analyzer.py`.

## Setup & Usage
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Set environment variables:** (see `.env.copy` for required keys)
3. **Run the server:**
   ```bash
   python pr_analyzer.py
   ```

## High-Level Architecture Diagram

```
flowchart TD
    subgraph github_ops
        A[auth.py]
        B[pr_tools.py]
        C[repo_tools.py]
        D[ci_tools.py]
        E[testgen.py]
    end
    F[pr_analyzer.py] -->|registers tools| B
    F --> C
    F --> D
    F --> E
    F --> A
    B -->|uses| A
    C -->|uses| A
    D -->|uses| A
```

## License
MIT
