import sys
import os
import traceback
import base64
from typing import Any, List, Dict
from mcp.server.fastmcp import FastMCP
from ghub_integration import fetch_pr_changes
from notion_client import Client
from atlassian import Confluence
from dotenv import load_dotenv
import requests

class PRAnalyzer:
    def __init__(self) -> None:
        # Load env variables
        load_dotenv()

        # Initialize MCP server
        self.mcp = FastMCP("github_operations")
        print("MCP Server initialized", file=sys.stderr)

        # Initialize Notion Client
        self._init_notion()
        
        # Initialize Confluence Client
        self._init_confluence()

        # Initialize GitHub token
        self._init_github()

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

    def _init_github(self):
        """Initialize GitHub authentication"""
        try:
            self.github_token = os.getenv("GITHUB_TOKEN")
            if not self.github_token:
                raise ValueError("Missing GitHub token in environment variables")
            self.github_headers = {
                "Authorization": f"token {self.github_token}",
                "Accept": "application/vnd.github.v3+json"
            }
            print("GitHub authentication initialized successfully", file=sys.stderr)
        except Exception as e:
            print(f"Error initializing GitHub authentication: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            sys.exit(1)

    def _register_tools(self):
        """Register MCP tools for various GitHub operations"""
        
        # PR Analysis Tools
        @self.mcp.tool()
        async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
            """Fetch changes from a Github PR"""
            print(f"Fetching PR #{pr_number} from {repo_owner}/{repo_name}", file=sys.stderr)
            try:
                pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
                if pr_info is None:
                    print(f"No changes returned form fetch_pr_changes", file=sys.stderr)
                    return {"status": "error", "error": "No changes returned from fetch_pr_changes"}
                print(f"Successfully fetched PR information", file=sys.stderr)
                return {"status": "success", "data": pr_info}
            except Exception as e:
                print(f"Error fetching PR: {str(e)}", file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {"status": "error", "error": str(e)}

        @self.mcp.tool()
        async def create_notion_page(title: str, content: str) -> Dict[str, Any]:
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
                return {"status": "success", "message": f"Notion page '{title}' created successfully"}
            except Exception as e:
                error_msg = f"Error creating Notion page: {str(e)}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {"status": "error", "error": error_msg}
            
        @self.mcp.tool()
        async def create_confluence_page(title: str, content: str) -> Dict[str, Any]:
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
                    return {
                        "status": "success",
                        "message": f"Confluence page created successfully",
                        "url": page_url
                    }
                else:
                    raise Exception("Failed to create page - no page ID returned")
                    
            except Exception as e:
                error_msg = f"Error creating Confluence page: {str(e)}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {"status": "error", "error": error_msg}

        # Repository Management Tools
        @self.mcp.tool()
        async def create_repository(name: str, description: str, private: bool = True) -> Dict[str, Any]:
            """Create a new GitHub repository"""
            print(f"Creating repository: {name}", file=sys.stderr)
            try:
                response = requests.post(
                    "https://api.github.com/user/repos",
                    headers=self.github_headers,
                    json={
                        "name": name,
                        "description": description,
                        "private": private
                    }
                )
                response.raise_for_status()
                repo_data = response.json()
                print(f"Repository '{name}' created successfully!", file=sys.stderr)
                return {
                    "status": "success",
                    "data": {
                        "name": repo_data["name"],
                        "url": repo_data["html_url"],
                        "clone_url": repo_data["clone_url"]
                    }
                }
            except Exception as e:
                error_msg = f"Error creating repository: {str(e)}"
                print(error_msg, file=sys.stderr)
                traceback.print_exc(file=sys.stderr)
                return {"status": "error", "error": error_msg}

        @self.mcp.tool()
        async def setup_repository_template(repo_owner: str, repo_name: str, template_name: str) -> Dict[str, Any]:
            """Set up a repository with a predefined template"""
            try:
                # Basic input validation
                if not all([repo_owner, repo_name, template_name]):
                    return {
                        "status": "error",
                        "error": "Missing required parameters"
                    }

                # Basic templates with minimal required files
                templates = {
                    "python": {
                        "files": [
                            {"path": "requirements.txt", "content": ""},
                            {"path": ".gitignore", "content": "*.pyc\n__pycache__/\n.env"}
                        ]
                    },
                    "node": {
                        "files": [
                            {"path": "package.json", "content": "{}"},
                            {"path": ".gitignore", "content": "node_modules/\n.env"}
                        ]
                    },
                    "angular": {
                        "files": [
                            {"path": "package.json", "content": "{\n  \"name\": \"angular-project\",\n  \"version\": \"0.0.0\",\n  \"scripts\": {\n    \"ng\": \"ng\",\n    \"start\": \"ng serve\",\n    \"build\": \"ng build\",\n    \"watch\": \"ng build --watch --configuration development\",\n    \"test\": \"ng test\"\n  },\n  \"private\": true\n}"},
                            {"path": ".gitignore", "content": "/dist\n/tmp\n/out-tsc\n/bazel-out\n\n# dependencies\n/node_modules\n\n# profiling files\nchrome-profiler-events*.json\nspeed-measure-plugin*.json\n\n# IDEs and editors\n.idea/\n.project\n.classpath\n.c9/\n*.launch\n.settings/\n*.sublime-workspace\n\n# Visual Studio Code\n.vscode/*\n!.vscode/settings.json\n!.vscode/tasks.json\n!.vscode/launch.json\n!.vscode/extensions.json\n.history/*\n\n# Miscellaneous\n/.angular/cache\n.sass-cache/\n/connect.lock\n/coverage\n/libpeerconnection.log\ntestem.log\n/typings\n\n# System files\n.DS_Store\nThumbs.db"}
                        ]
                    },
                    "java": {
                        "files": [
                            {"path": "pom.xml", "content": "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<project xmlns=\"http://maven.apache.org/POM/4.0.0\"\n         xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\"\n         xsi:schemaLocation=\"http://maven.apache.org/POM/4.0.0 http://maven.apache.org/xsd/maven-4.0.0.xsd\">\n    <modelVersion>4.0.0</modelVersion>\n\n    <groupId>com.example</groupId>\n    <artifactId>java-project</artifactId>\n    <version>1.0-SNAPSHOT</version>\n\n    <properties>\n        <maven.compiler.source>11</maven.compiler.source>\n        <maven.compiler.target>11</maven.compiler.target>\n    </properties>\n</project>"},
                            {"path": ".gitignore", "content": "target/\n!.mvn/wrapper/maven-wrapper.jar\n!**/src/main/**/target/\n!**/src/test/**/target/\n\n### STS ###\n.apt_generated\n.classpath\n.factorypath\n.project\n.settings\n.springBeans\n.sts4-cache\n\n### IntelliJ IDEA ###\n.idea\n*.iws\n*.iml\n*.ipr\n\n### NetBeans ###\n/nbproject/private/\n/nbbuild/\n/dist/\n/nbdist/\n/.nb-gradle/\nbuild/\n!**/src/main/**/build/\n!**/src/test/**/build/\n\n### VS Code ###\n.vscode/\n\n### Mac OS ###\n.DS_Store"},
                            {"path": "src/main/java/com/example/App.java", "content": "package com.example;\n\npublic class App {\n    public static void main(String[] args) {\n        System.out.println(\"Hello World!\");\n    }\n}"}
                        ]
                    },
                    "golang": {
                        "files": [
                            {"path": "go.mod", "content": "module github.com/example/go-project\n\ngo 1.21"},
                            {"path": ".gitignore", "content": "# Binaries for programs and plugins\n*.exe\n*.exe~\n*.dll\n*.so\n*.dylib\n\n# Test binary, built with `go test -c`\n*.test\n\n# Output of the go coverage tool, specifically when used with LiteIDE\n*.out\n\n# Dependency directories (remove the comment below to include it)\nvendor/\n\n# Go workspace file\ngo.work\n\n# IDE specific files\n.idea/\n.vscode/\n*.swp\n*.swo\n\n# OS specific files\n.DS_Store\nThumbs.db"},
                            {"path": "main.go", "content": "package main\n\nimport \"fmt\"\n\nfunc main() {\n    fmt.Println(\"Hello, Go!\")\n}"}
                        ]
                    },
                    "php": {
                        "files": [
                            {"path": "composer.json", "content": "{\n    \"name\": \"example/php-project\",\n    \"description\": \"PHP Project\",\n    \"type\": \"project\",\n    \"require\": {\n        \"php\": \">=7.4\"\n    },\n    \"autoload\": {\n        \"psr-4\": {\n            \"App\\\\\": \"src/\"\n        }\n    }\n}"},
                            {"path": ".gitignore", "content": "/vendor/\n/vendor\n.env\n.env.backup\n.phpunit.result.cache\ncomposer.lock\n\n# IDE specific files\n.idea/\n.vscode/\n*.sublime-project\n*.sublime-workspace\n\n# OS specific files\n.DS_Store\nThumbs.db\n\n# PHP specific\n*.log\n*.cache\n*.swp\n*.swo"},
                            {"path": "index.php", "content": "<?php\n\necho \"Hello, PHP!\";\n"}
                        ]
                    }
                }

                # Validate template exists
                if template_name not in templates:
                    return {
                        "status": "error",
                        "error": f"Template '{template_name}' not found"
                    }

                # Verify repository access
                try:
                    response = requests.get(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                        headers=self.github_headers
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException as e:
                    return {
                        "status": "error",
                        "error": "Repository access verification failed"
                    }

                # Process template files
                template = templates[template_name]
                for file in template["files"]:
                    try:
                        # Base64 encode content (required by GitHub API)
                        content_bytes = file["content"].encode('utf-8')
                        content_base64 = base64.b64encode(content_bytes).decode('utf-8')

                        # Create file
                        response = requests.put(
                            f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file['path']}",
                            headers=self.github_headers,
                            json={
                                "message": f"Add {file['path']} from template",
                                "content": content_base64
                            }
                        )
                        response.raise_for_status()
                    except requests.exceptions.RequestException as e:
                        return {
                            "status": "error",
                            "error": f"Failed to create file {file['path']}"
                        }

                return {
                    "status": "success",
                    "message": f"Template {template_name} setup completed"
                }

            except Exception as e:
                return {
                    "status": "error",
                    "error": "Template setup failed"
                }

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