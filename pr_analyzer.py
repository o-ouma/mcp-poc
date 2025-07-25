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
from datetime import datetime, timedelta

class GithubOps:
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
        async def create_pull_request(
            repo_owner: str,
            repo_name: str,
            title: str,
            body: str,
            head_branch: str,
            base_branch: str = "main"
        ) -> Dict[str, Any]:
            """Create a GitHub Pull Request"""
            try:
                # Validate required parameters
                if not all([repo_owner, repo_name, title, head_branch]):
                    return {
                        "status": "error",
                        "error": "Missing required parameters: repo_owner, repo_name, title, and head_branch are required"
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

                # Create the pull request
                try:
                    response = requests.post(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls",
                        headers=self.github_headers,
                        json={
                            "title": title,
                            "body": body,
                            "head": head_branch,
                            "base": base_branch
                        }
                    )
                    response.raise_for_status()
                    pr_data = response.json()

                    return {
                        "status": "success",
                        "data": {
                            "number": pr_data["number"],
                            "title": pr_data["title"],
                            "url": pr_data["html_url"],
                            "state": pr_data["state"],
                            "created_at": pr_data["created_at"]
                        }
                    }
                except requests.exceptions.RequestException as e:
                    if response.status_code == 422:
                        return {
                            "status": "error",
                            "error": "Pull request creation failed: Branch may not exist or PR already exists"
                        }
                    return {
                        "status": "error",
                        "error": f"Failed to create pull request: {str(e)}"
                    }

            except Exception as e:
                return {
                    "status": "error",
                    "error": "Pull request creation failed"
                }

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

        @self.mcp.tool()
        async def create_dockerfile(
            repo_owner: str,
            repo_name: str,
            language: str,
            port: int = None
        ) -> Dict[str, Any]:
            """Create a Dockerfile for the project based on its language
            
            Args:
                repo_owner: Repository owner/organization
                repo_name: Repository name
                language: Project language (python, node, java, golang, php, angular)
                port: Optional port to expose (defaults to language-specific port)
            """
            try:
                # Validate required parameters
                if not all([repo_owner, repo_name, language]):
                    return {
                        "status": "error",
                        "error": "Missing required parameters: repo_owner, repo_name, and language are required"
                    }

                # Set default ports if not specified
                default_ports = {
                    "python": 8000,
                    "node": 3000,
                    "java": 8080,
                    "golang": 8080,
                    "php": 80,
                    "angular": 4200
                }
                
                if port is None:
                    port = default_ports.get(language, 8080)

                # Define Dockerfile templates for each language
                dockerfile_templates = {
                    "python": f"""# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE {port}

# Run the application
CMD ["python", "app.py"]""",

                    "node": f"""# Use Node.js LTS slim image
FROM node:20-slim

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Build the application
RUN npm run build

# Expose port
EXPOSE {port}

# Run the application
CMD ["npm", "start"]""",

                    "java": f"""# Use OpenJDK 17 slim image
FROM eclipse-temurin:17-jre-jammy

# Set working directory
WORKDIR /app

# Copy the JAR file
COPY target/*.jar app.jar

# Expose port
EXPOSE {port}

# Run the application
CMD ["java", "-jar", "app.jar"]""",

                    "golang": f"""# Build stage
FROM golang:1.21-alpine AS builder

# Set working directory
WORKDIR /app

# Copy go mod files
COPY go.mod go.sum ./

# Download dependencies
RUN go mod download

# Copy source code
COPY . .

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -o main .

# Final stage
FROM alpine:latest

# Set working directory
WORKDIR /app

# Copy binary from builder
COPY --from=builder /app/main .

# Expose port
EXPOSE {port}

# Run the application
CMD ["./main"]""",

                    "php": f"""# Use PHP 8.2 Apache image
FROM php:8.2-apache

# Set working directory
WORKDIR /var/www/html

# Install PHP extensions and dependencies
RUN apt-get update && apt-get install -y \\
    libzip-dev \\
    zip \\
    && docker-php-ext-install zip pdo pdo_mysql

# Copy project files
COPY . .

# Set permissions
RUN chown -R www-data:www-data /var/www/html

# Expose port
EXPOSE {port}

# Apache configuration
RUN a2enmod rewrite
CMD ["apache2-foreground"]""",

                    "angular": f"""# Build stage
FROM node:20-slim AS builder

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy project files
COPY . .

# Build the application
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built assets from builder
COPY --from=builder /app/dist/* /usr/share/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE {port}

# Start nginx
CMD ["nginx", "-g", "daemon off;"]"""
                }

                if language not in dockerfile_templates:
                    return {
                        "status": "error",
                        "error": f"Unsupported language: {language}. Supported languages: {', '.join(dockerfile_templates.keys())}"
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

                # Check if Dockerfile already exists
                try:
                    response = requests.get(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/Dockerfile",
                        headers=self.github_headers
                    )
                    if response.status_code == 200:
                        return {
                            "status": "error",
                            "error": "Dockerfile already exists in the repository"
                        }
                except requests.exceptions.RequestException:
                    pass  # File doesn't exist, proceed with creation

                # Create Dockerfile
                try:
                    dockerfile_content = dockerfile_templates[language]
                    content_bytes = dockerfile_content.encode('utf-8')
                    content_base64 = base64.b64encode(content_bytes).decode('utf-8')

                    response = requests.put(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/Dockerfile",
                        headers=self.github_headers,
                        json={
                            "message": f"Add Dockerfile for {language} project",
                            "content": content_base64
                        }
                    )
                    response.raise_for_status()

                    return {
                        "status": "success",
                        "data": {
                            "message": f"Dockerfile created for {language} project",
                            "port": port,
                            "url": response.json()["content"]["html_url"]
                        }
                    }

                except requests.exceptions.RequestException as e:
                    return {
                        "status": "error",
                        "error": f"Failed to create Dockerfile: {str(e)}"
                    }

            except Exception as e:
                return {
                    "status": "error",
                    "error": "Dockerfile creation failed"
                }

        @self.mcp.tool()
        async def analyze_pipeline_results(
            repo_owner: str,
            repo_name: str,
            workflow_id: str = None,
            run_id: str = None,
            days: int = 7
        ) -> Dict[str, Any]:
            """Analyze GitHub Actions pipeline results and provide recommendations
            
            Args:
                repo_owner: Repository owner/organization
                repo_name: Repository name
                workflow_id: Specific workflow ID to analyze (optional)
                run_id: Specific run ID to analyze (optional)
                days: Number of days to analyze (default: 7)
            """
            try:
                # Validate required parameters
                if not all([repo_owner, repo_name]):
                    return {
                        "status": "error",
                        "error": "Missing required parameters: repo_owner and repo_name are required"
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

                # Get workflow runs
                try:
                    if run_id:
                        # Get specific run
                        response = requests.get(
                            f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs/{run_id}",
                            headers=self.github_headers
                        )
                        response.raise_for_status()
                        runs = [response.json()]
                    else:
                        # Get workflow runs
                        url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/actions/runs"
                        if workflow_id:
                            url += f"/workflows/{workflow_id}"
                        response = requests.get(
                            url,
                            headers=self.github_headers,
                            params={"per_page": 100}
                        )
                        response.raise_for_status()
                        runs = response.json()["workflow_runs"]

                    # Filter runs by date if needed
                    if days and not run_id:
                        cutoff_date = datetime.now() - timedelta(days=days)
                        runs = [run for run in runs if datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ") > cutoff_date]

                    # Analyze runs
                    total_runs = len(runs)
                    if total_runs == 0:
                        return {
                            "status": "error",
                            "error": "No pipeline runs found for the specified criteria"
                        }

                    # Calculate statistics
                    successful_runs = sum(1 for run in runs if run["conclusion"] == "success")
                    failed_runs = sum(1 for run in runs if run["conclusion"] == "failure")
                    cancelled_runs = sum(1 for run in runs if run["conclusion"] == "cancelled")
                    
                    # Calculate average duration
                    durations = []
                    for run in runs:
                        if run["conclusion"] in ["success", "failure"]:
                            start_time = datetime.strptime(run["created_at"], "%Y-%m-%dT%H:%M:%SZ")
                            end_time = datetime.strptime(run["updated_at"], "%Y-%m-%dT%H:%M:%SZ")
                            duration = (end_time - start_time).total_seconds() / 60  # in minutes
                            durations.append(duration)
                    
                    avg_duration = sum(durations) / len(durations) if durations else 0

                    # Generate recommendations
                    recommendations = []
                    
                    # Success rate recommendations
                    success_rate = (successful_runs / total_runs) * 100
                    if success_rate < 80:
                        recommendations.append({
                            "type": "success_rate",
                            "priority": "high",
                            "message": f"Low success rate ({success_rate:.1f}%). Review recent failures and consider improving test coverage."
                        })
                    
                    # Duration recommendations
                    if avg_duration > 30:  # More than 30 minutes
                        recommendations.append({
                            "type": "duration",
                            "priority": "medium",
                            "message": f"Long average pipeline duration ({avg_duration:.1f} minutes). Consider optimizing pipeline steps or using caching."
                        })
                    
                    # Failure pattern analysis
                    if failed_runs > 0:
                        # Get detailed failure information for recent failed runs
                        recent_failures = []
                        for run in runs:
                            if run["conclusion"] == "failure":
                                try:
                                    jobs_response = requests.get(
                                        run["jobs_url"],
                                        headers=self.github_headers
                                    )
                                    jobs_response.raise_for_status()
                                    jobs = jobs_response.json()["jobs"]
                                    
                                    for job in jobs:
                                        if job["conclusion"] == "failure":
                                            recent_failures.append({
                                                "job_name": job["name"],
                                                "failed_at": job["completed_at"]
                                            })
                                except requests.exceptions.RequestException:
                                    continue
                        
                        if recent_failures:
                            # Group failures by job name
                            failure_patterns = {}
                            for failure in recent_failures:
                                job_name = failure["job_name"]
                                if job_name not in failure_patterns:
                                    failure_patterns[job_name] = 0
                                failure_patterns[job_name] += 1
                            
                            # Add recommendations for frequent failures
                            for job_name, count in failure_patterns.items():
                                if count >= 2:  # Job failed at least twice
                                    recommendations.append({
                                        "type": "failure_pattern",
                                        "priority": "high",
                                        "message": f"Job '{job_name}' failed {count} times. Review and fix recurring issues."
                                    })

                    return {
                        "status": "success",
                        "data": {
                            "summary": {
                                "total_runs": total_runs,
                                "successful_runs": successful_runs,
                                "failed_runs": failed_runs,
                                "cancelled_runs": cancelled_runs,
                                "success_rate": f"{success_rate:.1f}%",
                                "average_duration": f"{avg_duration:.1f} minutes"
                            },
                            "recommendations": recommendations,
                            "recent_failures": recent_failures if failed_runs > 0 else []
                        }
                    }

                except requests.exceptions.RequestException as e:
                    return {
                        "status": "error",
                        "error": f"Failed to fetch pipeline data: {str(e)}"
                    }

            except Exception as e:
                return {
                    "status": "error",
                    "error": "Pipeline analysis failed"
                }

        @self.mcp.tool()
        async def merge_pull_request(
            repo_owner: str,
            repo_name: str,
            pr_number: int,
            merge_method: str = "merge",
            commit_title: str = None,
            commit_message: str = None
        ) -> Dict[str, Any]:
            """Merge a GitHub Pull Request
            
            Args:
                repo_owner: Repository owner/organization
                repo_name: Repository name
                pr_number: Pull request number
                merge_method: Merge strategy (merge, squash, or rebase)
                commit_title: Custom merge commit title (optional)
                commit_message: Custom merge commit message (optional)
            """
            try:
                # Validate required parameters
                if not all([repo_owner, repo_name, pr_number]):
                    return {
                        "status": "error",
                        "error": "Missing required parameters: repo_owner, repo_name, and pr_number are required"
                    }

                # Validate merge method
                valid_merge_methods = ["merge", "squash", "rebase"]
                if merge_method not in valid_merge_methods:
                    return {
                        "status": "error",
                        "error": f"Invalid merge method. Must be one of: {', '.join(valid_merge_methods)}"
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

                # Prepare merge payload
                merge_payload = {
                    "merge_method": merge_method
                }
                if commit_title:
                    merge_payload["commit_title"] = commit_title
                if commit_message:
                    merge_payload["commit_message"] = commit_message

                # Attempt to merge the PR
                try:
                    response = requests.put(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/merge",
                        headers=self.github_headers,
                        json=merge_payload
                    )
                    
                    if response.status_code == 200:
                        merge_data = response.json()
                        return {
                            "status": "success",
                            "data": {
                                "sha": merge_data.get("sha"),
                                "merged": merge_data.get("merged"),
                                "message": merge_data.get("message")
                            }
                        }
                    elif response.status_code == 405:
                        return {
                            "status": "error",
                            "error": "Pull request is not mergeable"
                        }
                    elif response.status_code == 409:
                        return {
                            "status": "error",
                            "error": "Pull request has conflicts that need to be resolved"
                        }
                    else:
                        response.raise_for_status()

                except requests.exceptions.RequestException as e:
                    return {
                        "status": "error",
                        "error": f"Failed to merge pull request: {str(e)}"
                    }

            except Exception as e:
                return {
                    "status": "error",
                    "error": "Pull request merge failed"
                }

        @self.mcp.tool()
        async def generate_readme(
            repo_owner: str,
            repo_name: str,
            language: str,
            project_title: str = None,
            project_description: str = None
        ) -> Dict[str, Any]:
            """Generate a README.md file for the project based on its language
            
            Args:
                repo_owner: Repository owner/organization
                repo_name: Repository name
                language: Project language (python, node, java, golang, php, angular)
                project_title: Optional project title (defaults to repo_name)
                project_description: Optional project description
            """
            try:
                # Validate required parameters
                if not all([repo_owner, repo_name, language]):
                    return {
                        "status": "error",
                        "error": "Missing required parameters: repo_owner, repo_name, and language are required"
                    }

                # Set defaults
                if not project_title:
                    project_title = repo_name
                if not project_description:
                    project_description = f"A {language} project."

                # Define README templates for each language
                readme_templates = {
                    "python": f"""# {{project_title}}

{{project_description}}

### Prerequisites

 - `Python`
 - `Docker`

## Project Setup

```bash
python3 -m venv venv
```

```bash
source venv/bin/activate
```

```bash
# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
# Run script
python app.py
```

### with Docker

```bash
# Build image
docker build -t app-image:1.0.0 .
```

```bash
# Run container
docker run --rm -d app-image:1.0.0
```

## Project Structure

- `app.py`: Main application file
- `requirements.txt`: Python dependencies
- `Dockerfile`
- `.env.copy`: Copy of .env file; Create .env file and paste content from the .env.copy

""",
                    "node": f"""# {{project_title}}

{{project_description}}

## Setup

```bash
# Install dependencies
npm install
```

## Usage

```bash
# Run server
npm start
```

### with Docker

```bash
# Build docker image
docker build -t app-image:1.0.0 .
```

```bash
# Run container
docker run --rm -d app-image:1.0.0
```

## Project Structure

- `package.json`: Project metadata and dependencies
- `index.js` or `app.js`: Main entry point
- `Dockerfile`
- `.env.copy`: Copy of .env file; Create .env file and paste content of .env.copy  

""",
                    "java": f"""# {{project_title}}

{{project_description}}

## Build

```bash
mvn package
```

## Run

```bash
java -jar target/app.jar
```

## Project Structure

- `src/main/java/`: Java source files
- `pom.xml`: Maven configuration

""",
                    "golang": f"""# {{project_title}}

{{project_description}}

## Build

```bash
go build -o main .
```

## Run

```bash
./main
```

## Project Structure

- `main.go`: Main application file
- `go.mod`: Go module definition
- `Dockerfile`
- `.env.copy`: Copy of .env file; Create .env file and paste content from .env.copy

""",
                    "php": f"""# {{project_title}}

{{project_description}}

## Setup

Install dependencies (if using Composer):

```bash
composer install
```

## Usage

Run with PHP built-in server:

```bash
php -S localhost:8000
```

## Project Structure

- `index.php`: Main entry point
- `composer.json`: PHP dependencies
- `Dockerfile`
- `.env.copy`: Copy of .env file; Create .env file and paste content from .env.copy

""",
                    "angular": f"""# {{project_title}}

{{project_description}}

## Setup

```bash
npm install
```

## Development Server

```bash
ng serve
```

## Build

```bash
ng build
```

## Project Structure

- `src/`: Angular source files
- `package.json`: Project metadata and dependencies
- `Dockerfile`
- `.env.copy`: Copy of .env file; Create .env file and paste content from .env.copy

"""
                }

                if language not in readme_templates:
                    return {
                        "status": "error",
                        "error": f"Unsupported language: {language}. Supported languages: {', '.join(readme_templates.keys())}"
                    }

                # Render the README content
                readme_content = readme_templates[language].replace("{project_title}", project_title).replace("{project_description}", project_description)

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

                # Check if README.md already exists
                sha = None
                try:
                    response = requests.get(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/README.md",
                        headers=self.github_headers
                    )
                    if response.status_code == 200:
                        sha = response.json().get("sha")
                except requests.exceptions.RequestException:
                    pass  # File doesn't exist, proceed with creation

                # Create or update README.md
                try:
                    content_bytes = readme_content.encode('utf-8')
                    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                    payload = {
                        "message": f"Generate README.md for {language} project",
                        "content": content_base64
                    }
                    if sha:
                        payload["sha"] = sha
                    response = requests.put(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/README.md",
                        headers=self.github_headers,
                        json=payload
                    )
                    response.raise_for_status()
                    return {
                        "status": "success",
                        "data": {
                            "message": "README.md generated successfully",
                            "url": response.json()["content"]["html_url"]
                        }
                    }
                except requests.exceptions.RequestException as e:
                    return {
                        "status": "error",
                        "error": f"Failed to create/update README.md: {str(e)}"
                    }

            except Exception as e:
                return {
                    "status": "error",
                    "error": "README.md generation failed"
                }

        @self.mcp.tool()
        async def generate_tests() -> Dict[str, Any]:
            """Scan the repo for Python files and generate unittest stubs for each function/class in tests/ directory."""
            import ast
            import glob
            import pathlib

            repo_root = pathlib.Path(__file__).parent.resolve()
            tests_dir = repo_root / 'tests'
            tests_dir.mkdir(exist_ok=True)
            py_files = [
                f for f in glob.glob(str(repo_root / '**' / '*.py'), recursive=True)
                if not (str(f).startswith(str(tests_dir)) or '/venv/' in f or '/__pycache__/' in f or f.endswith('pr_analyzer.py'))
            ]
            results = []
            for py_file in py_files:
                rel_path = pathlib.Path(py_file).relative_to(repo_root)
                module_name = rel_path.stem
                test_file = tests_dir / f'test_{module_name}.py'
                with open(py_file, 'r', encoding='utf-8') as f:
                    source = f.read()
                try:
                    tree = ast.parse(source)
                except Exception as e:
                    results.append({"file": str(rel_path), "error": f"Parse error: {e}"})
                    continue
                test_lines = [
                    'import unittest',
                    f'import {module_name}',
                    '',
                ]
                for node in tree.body:
                    if isinstance(node, ast.FunctionDef):
                        test_lines.append(f'class Test{node.name.capitalize()}(unittest.TestCase):')
                        test_lines.append(f'    def test_{node.name}(self):')
                        test_lines.append(f'        # TODO: implement test for {node.name}')
                        test_lines.append(f'        self.assertTrue(True)')
                        test_lines.append('')
                    elif isinstance(node, ast.ClassDef):
                        test_lines.append(f'class Test{node.name}(unittest.TestCase):')
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and not item.name.startswith('__'):
                                test_lines.append(f'    def test_{item.name}(self):')
                                test_lines.append(f'        # TODO: implement test for {node.name}.{item.name}')
                                test_lines.append(f'        self.assertTrue(True)')
                                test_lines.append('')
                if len(test_lines) > 3:
                    with open(test_file, 'w', encoding='utf-8') as tf:
                        tf.write('\n'.join(test_lines))
                    results.append({"file": str(test_file.relative_to(repo_root)), "status": "created"})
                else:
                    results.append({"file": str(rel_path), "status": "no functions/classes found"})
            return {"status": "success", "results": results}

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
    analyzer = GithubOps()
    analyzer.run()