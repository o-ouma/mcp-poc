import sys
import os
import traceback
from typing import Any, List, Dict
from mcp.server.fastmcp import FastMCP
from ghub_integration import fetch_pr_changes
from notion_client import Client
from atlassian import Confluence
from dotenv import load_dotenv

class PRAnalyzer:
    def __init__(self) -> None:
        # Load env variables
        load_dotenv()

        # Initialize MCP server
        self.mcp = FastMCP("github_pr_analysis")
        print("MCP Server initialized", file=sys.stderr)

        # Initialize Notion Client
        self._init_notion()
        
        # Initialize Confluence Client
        self._init_confluence()

        # Register MCP tools
        self._register_tools()

    def _init_notion(self):
        """Initialize the Notion client with API key and page ID"""
        try:
            self.notion_api_key = os.getenv("NOTION_API_KEY")
            self.notion_page_id = os.getenv("NOTION_PAGE_ID")

            if not self.notion_api_key or not self.notion_page_id:
                raise ValueError("Missing Notion API key or page ID in environment variables")
            
            self.notion = Client(auth=self.notion_api_key)
            print(f"Notion client intialized successfully", file=sys.stderr)
            print(f"Using Notion page ID: {self.notion_page_id}", file=sys.stderr)
        except Exception as e:
            print(f"Error initializing Notion client: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    def _init_confluence(self):
        """Initialize the Confluence client with API credentials"""
        try:
            self.confluence_url = os.getenv("CONFLUENCE_URL")
            self.confluence_username = os.getenv("CONFLUENCE_USERNAME")
            self.confluence_api_token = os.getenv("CONFLUENCE_API_TOKEN")
            self.confluence_space_key = os.getenv("CONFLUENCE_SPACE_KEY")

            if not all([self.confluence_url, self.confluence_username, 
                       self.confluence_api_token, self.confluence_space_key]):
                raise ValueError("Missing Confluence credentials in environment variables")
            
            self.confluence = Confluence(
                url=self.confluence_url,
                username=self.confluence_username,
                password=self.confluence_api_token
            )
            print(f"Confluence client initialized successfully", file=sys.stderr)
            print(f"Using Confluence space key: {self.confluence_space_key}", file=sys.stderr)
        except Exception as e:
            print(f"Error initializing Confluence client: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    def _register_tools(self):
        """Register MCP tools for PR analysis with use of execution handler"""
        @self.mcp.tool()
        async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
            """Fetch changes from a Github PR"""
            print(f"Fetching PR #{pr_number} from {repo_owner}/{repo_name}", file=sys.stderr)
            try:
                pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
                if pr_info is None:
                    print(f"No changes returned form fetch_pr_changes", file=sys.stderr)
                    return {}
                print(f"Successfully fetched PR information", file=sys.stderr)
                return pr_info
            except Exception as e:
                print(f"Error fetching PR: {str(e)}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {}
            
        @self.mcp.tool()
        async def create_notion_page(title: str, content: str) -> str:
            """Create a Notion page with PR analysis"""
            print(f"Creating Notion page: {title}", file=sys.stderr)
            try:
                self.notion.pages.create(
                    parent={"type": "page_id", "page_id": self.notion_page_id},
                    properties={"title": {"title": [{"text": {"content": title}}]}},
                    children=[{
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{
                                "type": "text",
                                "text": {"content": content}
                            }]
                        }
                    }]
                )
                print(f"Notion page '{title}' created successfully!!", file=sys.stderr)
                return f"Notion page '{title}' created successfully!!"
            except Exception as e:
                error_msg = f"Error creating Notion page: {str(e)}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return error_msg
            
        @self.mcp.tool()
        async def create_confluence_page(title: str, content: str) -> str:
            """Create a Confluence page with PR analysis"""
            print(f"Creating Confluence page: {title}", file=sys.stderr)
            try:
                # Create the page in Confluence
                page = self.confluence.create_page(
                    space=self.confluence_space_key,
                    title=title,
                    body=content,
                    representation='storage'
                )
                
                if page and 'id' in page:
                    page_url = f"{self.confluence_url}/pages/viewpage.action?pageId={page['id']}"
                    print(f"Confluence page '{title}' created successfully!", file=sys.stderr)
                    return f"Confluence page created successfully! View it at: {page_url}"
                else:
                    raise Exception("Failed to create page - no page ID returned")
                    
            except Exception as e:
                error_msg = f"Error creating Confluence page: {str(e)}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return error_msg
            
    def run(self):
        """Start the MCP server"""
        try:
            print("Running MCP poc server for Github PR Analysis...", file=sys.stderr)
            self.mcp.run(transport="stdio")
        except Exception as e:
            print(f"Fatal Error in MCP poc Server: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    analyzer = PRAnalyzer()
    analyzer.run()