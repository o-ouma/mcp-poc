import sys
import traceback
from mcp.server.fastmcp import FastMCP
from github_ops.auth import (
    load_env,
    get_notion_client,
    get_confluence_client,
    get_github_headers,
    AuthError
)
from github_ops.pr_tools import register_pr_tools
from github_ops.repo_tools import register_repo_tools
from github_ops.ci_tools import register_ci_tools
from github_ops.testgen import register_testgen_tools


class GithubOps:
    def __init__(self) -> None:
        try:
            load_env()
            self.mcp = FastMCP("Github_Operations")
            print("MCP Server Initialized", file=sys.stderr)
            self.notion, self.notion_page_id = get_notion_client()
            self.confluence, self.confluence_space_key = get_confluence_client()
            self.github_headers = get_github_headers()
            # Register all tool groups
            register_pr_tools(
                self.mcp,
                self.github_headers,
                self.notion,
                self.notion_page_id,
                self.confluence,
                self.confluence_space_key
            )
            register_repo_tools(self.mcp, self.github_headers)
            register_ci_tools(self.mcp, self.github_headers)
            register_testgen_tools(self.mcp)
        except AuthError as e:
            print(f"Authentication error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    def run(self):
        """Start the MCP server"""
        try:
            print("Running MCP poc server for Github Ops...", file=sys.stderr)
            self.mcp.run(transport="stdio")
        except Exception as e:
            print(f"Ooops!! Fatal Error in MCP poc Server: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    g_operator = GithubOps()
    g_operator.run()