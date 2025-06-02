# Pull Request Analysis with MCP

## Prerequisites

1. Claude Desktop
2. Confluence Account
3. Notion Account
4. Python

Project leverages MCP to analyze PRs prior to merges, making the code review process easier. The results of the analysis are published to Notion and Confluence Pages.

As part of the analysis, the model also recommends improvements to each PR, further improving code quality.

Link to Notion page: https://www.notion.so/PR-Summaries-1f325dacde7e8015ba2dee4e9c8976ed

### Test Project

Create virtual environment:

`python3 -m venv venv`

Activate virtual environment:

`source venv/bin/activate`

Install dependencies:

`pip install -r requirements.txt`

Run script/mcp tools:

`python pr_analyzer.py`