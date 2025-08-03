import sys
import traceback
import base64
from typing import Any, Dict
import requests

def register_repo_tools(mcp, github_headers):
    """
    Register MCP tools related to repository management (create repo, setup template, Dockerfile, README)
    """
    # Create repository
    @mcp.tool()
    async def create_repository(name: str, description: str, private: bool = True) -> Dict[str, Any]:
        """Create a new GitHub repository"""
        print(f"Creating repository: {name}", file=sys.stderr)
        try:
            response = requests.post(
                "https://api.github.com/user/repos",
                headers=github_headers,
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

    # Setup repository template
    @mcp.tool()
    async def setup_repository_template(repo_owner: str, repo_name: str, template_name: str) -> Dict[str, Any]:
        """Set up a repository with a predefined template"""
        try:
            if not all([repo_owner, repo_name, template_name]):
                return {
                    "status": "error",
                    "error": "Missing required parameters"
                }
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
                        {"path": "composer.json", "content": "{\n    \"name\": \"example/php-project\",\n    \"description\": \"PHP Project\",\n    \"type\": \"project\",\n    \"require\": {\n        \"php\": \"\u003e=7.4\"\n    },\n    \"autoload\": {\n        \"psr-4\": {\n            \"App\\\\\": \"src/\"\n        }\n    }\n}"},
                        {"path": ".gitignore", "content": "/vendor/\n/vendor\n.env\n.env.backup\n.phpunit.result.cache\ncomposer.lock\n\n# IDE specific files\n.idea/\n.vscode/\n*.sublime-project\n*.sublime-workspace\n\n# OS specific files\n.DS_Store\nThumbs.db\n\n# PHP specific\n*.log\n*.cache\n*.swp\n*.swo"},
                        {"path": "index.php", "content": "<?php\n\necho \"Hello, PHP!\";\n"}
                    ]
                }
            }
            if template_name not in templates:
                return {
                    "status": "error",
                    "error": f"Template '{template_name}' not found"
                }
            # Verify repo access
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                    headers=github_headers
                )
                response.raise_for_status()
            except requests.exceptions.RequestException:
                return {
                    "status": "error",
                    "error": "Repository access verification failed"
                }
            # Create files from template
            template = templates[template_name]
            for file in template["files"]:
                try:
                    content_bytes = file["content"].encode('utf-8')
                    content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                    response = requests.put(
                        f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/{file['path']}",
                        headers=github_headers,
                        json={
                            "message": f"Add {file['path']} from template",
                            "content": content_base64
                        }
                    )
                    response.raise_for_status()
                except requests.exceptions.RequestException:
                    return {
                        "status": "error",
                        "error": f"Failed to create file {file['path']}"
                    }
            return {
                "status": "success",
                "message": f"Template {template_name} setup completed"
            }
        except Exception:
            return {
                "status": "error",
                "error": "Template setup failed"
            }

    # Create Dockerfile
    @mcp.tool()
    async def create_dockerfile(
        repo_owner: str,
        repo_name: str,
        language: str,
        port: int = None
    ) -> Dict[str, Any]:
        """Create a Dockerfile for the project based on its language"""
        try:
            if not all([repo_owner, repo_name, language]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: repo_owner, repo_name, and language are required"
                }
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
            dockerfile_templates = {
                "python": f"""# Use Python 3.11 slim image\nFROM python:3.11-slim\n\n# Set working directory\nWORKDIR /app\n\n# Copy requirements file\nCOPY requirements.txt .\n\n# Install dependencies\nRUN pip install --no-cache-dir -r requirements.txt\n\n# Copy project files\nCOPY . .\n\n# Expose port\nEXPOSE {port}\n\n# Run the application\nCMD [\"python\", \"app.py\"]""",
                "node": f"""# Use Node.js LTS slim image\nFROM node:20-slim\n\n# Set working directory\nWORKDIR /app\n\n# Copy package files\nCOPY package*.json ./\n\n# Install dependencies\nRUN npm install\n\n# Copy project files\nCOPY . .\n\n# Build the application\nRUN npm run build\n\n# Expose port\nEXPOSE {port}\n\n# Run the application\nCMD [\"npm\", \"start\"]""",
                "java": f"""# Use OpenJDK 17 slim image\nFROM eclipse-temurin:17-jre-jammy\n\n# Set working directory\nWORKDIR /app\n\n# Copy the JAR file\nCOPY target/*.jar app.jar\n\n# Expose port\nEXPOSE {port}\n\n# Run the application\nCMD [\"java\", \"-jar\", \"app.jar\"]""",
                "golang": f"""# Build stage\nFROM golang:1.21-alpine AS builder\n\n# Set working directory\nWORKDIR /app\n\n# Copy go mod files\nCOPY go.mod go.sum ./\n\n# Download dependencies\nRUN go mod download\n\n# Copy source code\nCOPY . .\n\n# Build the application\nRUN CGO_ENABLED=0 GOOS=linux go build -o main .\n\n# Final stage\nFROM alpine:latest\n\n# Set working directory\nWORKDIR /app\n\n# Copy binary from builder\nCOPY --from=builder /app/main .\n\n# Expose port\nEXPOSE {port}\n\n# Run the application\nCMD [\"./main\"]""",
                "php": f"""# Use PHP 8.2 Apache image\nFROM php:8.2-apache\n\n# Set working directory\nWORKDIR /var/www/html\n\n# Install PHP extensions and dependencies\nRUN apt-get update && apt-get install -y \\\n    libzip-dev \\\n    zip \\\n    && docker-php-ext-install zip pdo pdo_mysql\n\n# Copy project files\nCOPY . .\n\n# Set permissions\nRUN chown -R www-data:www-data /var/www/html\n\n# Expose port\nEXPOSE {port}\n\n# Apache configuration\nRUN a2enmod rewrite\nCMD [\"apache2-foreground\"]""",
                "angular": f"""# Build stage\nFROM node:20-slim AS builder\n\n# Set working directory\nWORKDIR /app\n\n# Copy package files\nCOPY package*.json ./\n\n# Install dependencies\nRUN npm install\n\n# Copy project files\nCOPY . .\n\n# Build the application\nRUN npm run build\n\n# Production stage\nFROM nginx:alpine\n\n# Copy built assets from builder\nCOPY --from=builder /app/dist/* /usr/share/nginx/html/\n\n# Copy nginx configuration\nCOPY nginx.conf /etc/nginx/conf.d/default.conf\n\n# Expose port\nEXPOSE {port}\n\n# Start nginx\nCMD [\"nginx\", "-g", "daemon off;\"]"""
            }
            if language not in dockerfile_templates:
                return {
                    "status": "error",
                    "error": f"Unsupported language: {language}. Supported languages: {', '.join(dockerfile_templates.keys())}"
                }
            # Verify repo access
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                    headers=github_headers
                )
                response.raise_for_status()
            except requests.exceptions.RequestException:
                return {
                    "status": "error",
                    "error": "Repository access verification failed"
                }
            # Check if Dockerfile already exists
            sha = None
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/Dockerfile",
                    headers=github_headers
                )
                if response.status_code == 200:
                    return {
                        "status": "error",
                        "error": "Dockerfile already exists in the repository"
                    }
            except requests.exceptions.RequestException:
                pass  # File doesn't exist, proceed
            # Create Dockerfile
            try:
                dockerfile_content = dockerfile_templates[language]
                content_bytes = dockerfile_content.encode('utf-8')
                content_base64 = base64.b64encode(content_bytes).decode('utf-8')
                response = requests.put(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/Dockerfile",
                    headers=github_headers,
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
        except Exception:
            return {
                "status": "error",
                "error": "Dockerfile creation failed"
            }

    # Generate README.md
    @mcp.tool()
    async def generate_readme(
        repo_owner: str,
        repo_name: str,
        language: str,
        project_title: str = None,
        project_description: str = None
    ) -> Dict[str, Any]:
        """Generate a README.md file for the project based on its language"""
        try:
            if not all([repo_owner, repo_name, language]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: repo_owner, repo_name, and language are required"
                }
            if not project_title:
                project_title = repo_name
            if not project_description:
                project_description = f"A {language} project."
            readme_templates = {
                "python": f"""# {{project_title}}\n\n{{project_description}}\n\n### Prerequisites\n\n - `Python`\n - `Docker`\n\n## Project Setup\n\n```bash\npython3 -m venv venv\n```\n\n```bash\nsource venv/bin/activate\n```\n\n```bash\n# Install dependencies\npip install -r requirements.txt\n```\n\n## Usage\n\n```bash\n# Run script\npython app.py\n```\n\n### with Docker\n\n```bash\n# Build image\ndocker build -t app-image:1.0.0 .\n```\n\n```bash\n# Run container\ndocker run --rm -d app-image:1.0.0\n```\n\n## Project Structure\n\n- `app.py`: Main application file\n- `requirements.txt`: Python dependencies\n- `Dockerfile`\n- `.env.copy`: Copy of .env file; Create .env file and paste content from the .env.copy\n\n""",
                "node": f"""# {{project_title}}\n\n{{project_description}}\n\n## Setup\n\n```bash\n# Install dependencies\nnpm install\n```\n\n## Usage\n\n```bash\n# Run server\nnpm start\n```\n\n### with Docker\n\n```bash\n# Build docker image\ndocker build -t app-image:1.0.0 .\n```\n\n```bash\n# Run container\ndocker run --rm -d app-image:1.0.0\n```\n\n## Project Structure\n\n- `package.json`: Project metadata and dependencies\n- `index.js` or `app.js`: Main entry point\n- `Dockerfile`\n- `.env.copy`: Copy of .env file; Create .env file and paste content of .env.copy  \n\n""",
                "java": f"""# {{project_title}}\n\n{{project_description}}\n\n## Build\n\n```bash\nmvn package\n```\n\n## Run\n\n```bash\njava -jar target/app.jar\n```\n\n## Project Structure\n\n- `src/main/java/`: Java source files\n- `pom.xml`: Maven configuration\n\n""",
                "golang": f"""# {{project_title}}\n\n{{project_description}}\n\n## Build\n\n```bash\ngo build -o main .\n```\n\n## Run\n\n```bash\n./main\n```\n\n## Project Structure\n\n- `main.go`: Main application file\n- `go.mod`: Go module definition\n- `Dockerfile`\n- `.env.copy`: Copy of .env file; Create .env file and paste content from .env.copy\n\n""",
                "php": f"""# {{project_title}}\n\n{{project_description}}\n\n## Setup\n\nInstall dependencies (if using Composer):\n\n```bash\ncomposer install\n```\n\n## Usage\n\nRun with PHP built-in server:\n\n```bash\nphp -S localhost:8000\n```\n\n## Project Structure\n\n- `index.php`: Main entry point\n- `composer.json`: PHP dependencies\n- `Dockerfile`\n- `.env.copy`: Copy of .env file; Create .env file and paste content from .env.copy\n\n""",
                "angular": f"""# {{project_title}}\n\n{{project_description}}\n\n## Setup\n\n```bash\nnpm install\n```\n\n## Development Server\n\n```bash\nng serve\n```\n\n## Build\n\n```bash\nng build\n```\n\n## Project Structure\n\n- `src/`: Angular source files\n- `package.json`: Project metadata and dependencies\n- `Dockerfile`\n- `.env.copy`: Copy of .env file; Create .env file and paste content from .env.copy\n\n"""
            }
            if language not in readme_templates:
                return {
                    "status": "error",
                    "error": f"Unsupported language: {language}. Supported languages: {', '.join(readme_templates.keys())}"
                }
            # Verify repo access
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                    headers=github_headers
                )
                response.raise_for_status()
            except requests.exceptions.RequestException:
                return {
                    "status": "error",
                    "error": "Repository access verification failed"
                }
            # Check if README.md already exists
            sha = None
            try:
                response = requests.get(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}/contents/README.md",
                    headers=github_headers
                )
                if response.status_code == 200:
                    sha = response.json().get("sha")
            except requests.exceptions.RequestException:
                pass  # File doesn't exist, proceed
            # Create or update README.md
            try:
                readme_content = readme_templates[language].replace("{project_title}", project_title).replace("{project_description}", project_description)
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
                    headers=github_headers,
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
        except Exception:
            return {
                "status": "error",
                "error": "README.md generation failed"
            } 