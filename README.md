# Pull Request Analysis with MCP

## Prerequisites

1. Claude Desktop
2. Confluence Account
3. Notion Account
4. Python

Project leverages MCP to:

 1. Analyze PRs prior to merges, making the code review process easier. The results of the analysis are published to Notion and Confluence Pages.

 2. Create a github repo

 3. Create a PR

 4. Merge a PR

As part of the analysis, the model also recommends improvements to each PR, further improving code quality.

Link to Notion page: https://www.notion.so/PR-Summaries-1f325dacde7e8015ba2dee4e9c8976ed

### Test Project

Create and populate your .env file with variables defined in .env.copy

Create virtual environment:

`python3 -m venv venv`

Activate virtual environment:

`source venv/bin/activate`

Install dependencies:

`pip install -r requirements.txt`

Run script/mcp tools:

`python pr_analyzer.py`


Launch claude desktop and test with prompt below:

`Analyze this github pull request: https://github.com/o-ouma/mcp-poc/pull/6`

After analysis claude publishes the PR analysis summary to notion and confluence pages


### To Do:

1. Add create repo feature
2. Add repo templates for python, node, angular, golang etc.
3. Add feature to create PR
4. Merge PR feature
5. Analyze pipeline results



