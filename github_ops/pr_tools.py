import sys
import traceback
from typing import Any, Dict
from ghub_integration import fetch_pr_changes
import requests

def register_pr_tools(mcp, github_headers, notion, notion_page_id, confluence, confluence_space_key):
    """
    Register MCP tools related to PRs
    """

    # Fetch PR
    @mcp.tool()
    async def fetch_pr(repo_owner: str, repo_name: str, pr_number: int) -> Dict[str, Any]:
        """Fetch changes from Github PR"""
        print(f"Fetching PR #{pr_number} from {repo_owner}/{repo_name}", file=sys.stderr)
        try:
            pr_info = fetch_pr_changes(repo_owner, repo_name, pr_number)
            if pr_info is None:
                print(f"No changes returned from fetch_pr_changes", file=sys.stderr)
                return {"status": "error", "error": "No changes returned from fetch_pr_changes"}
            print(f"Successfully fetched PR information", file=sys.stderr)
            return {"status": "success", "data": pr_info}
        except Exception as e:
            print(f"Error fetching PR: {str(e)}", file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"status": "error", "error": str(e)}
        
    # Create PR
    @mcp.tool()
    async def create_pull_request(
        repo_owner: str,
        repo_name: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main"
    ) -> Dict[str, Any]:
        """Create a Github PR"""
        try:
            if not all([repo_owner, repo_name, title, head_branch]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: repo_owner, repo_name, title and head_branch are all required"
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
            # Create PR
            try:
                response = requests.post(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}",
                    headers=github_headers,
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
                        "error": "PR creation failed: Branch may not exist or PR already exists"
                    }
                return {
                    "status": "error",
                    "error": f"Failed to create PR: {str(e)}"
                }
        except Exception:
            return {
                "status": "error",
                "error": "PR creation failed"
            }
    
    # Merge PR
    @mcp.tool()
    async def merge_pull_request(
        repo_owner: str,
        repo_name: str,
        pr_number: int,
        merge_method: str = "merge",
        commit_title: str = None,
        commit_message: str = None
    ) -> Dict[str, Any]:
        """Merge a Github PR"""
        try:
            if not all([repo_owner, repo_name, pr_number]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: repo_owner, repo_name and pr_number are required"
                }
            valid_merge_methods = ["merge", "squash", "rebase"]
            if merge_method not in valid_merge_methods:
                return {
                    "status": "error",
                    "error": f"Invalid merge method. Must be one of: {', '.join(valid_merge_methods)}"
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
            # Prepare merge payload
            merge_payload = {
                "merge_method": merge_method
            }
            if commit_title:
                merge_payload["commit_title"] = commit_title
            if commit_message:
                merge_payload["commit_message"] = commit_message

            # Attempt to merge PR
            try:
                response = requests.put(
                    f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls/{pr_number}/merge",
                    headers=github_headers,
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
                        "error": "PR cannot be merged because of forbidden permissions"
                    }
                elif response.status_code == 409:
                    return {
                        "status": "error",
                        "error": "PR has conflicts that need to be resolved"
                    }
                else:
                    response.raise_for_status()
            except requests.exceptions.RequestException as e:
                return {
                    "status": "error",
                    "error": f"Failed to merge PR: {str(e)}"
                }
        except Exception:
            return {
                "status": "error",
                "error": "Pull request merge failed"
            }
    
    # Create Notion page after PR analysis
    @mcp.tool()
    async def create_notion_page(title: str, content: str) -> Dict[str, Any]:
        """Create a Notion page with PR Analysis"""
        print(f"Creating Notion page: {title}", file=sys.stderr)
        try:
            notion.pages.create(
                parent={"type": "page_id", "page_id": notion_page_id},
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
            print(f"Notion page '{title}' created successfully!", file=sys.stderr)
            return {"status": "success", "message": f"Notion page '{title}' created successfully"}
        except Exception as e:
            error_msg = f"Error creating Notion page: {str(e)}"
            print(error_msg, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"status": "error", "error": error_msg}

    # Create confluence page after PR analysis    
    @mcp.tool()
    async def create_confluence_page(title: str, content: str) -> Dict[str, Any]:
        """Create a Confluence page with PR analysis"""
        print(f"Creating Confluence page: {title}", file=sys.stderr)
        try:
            page = confluence.create_page(
                space=confluence_space_key,
                title=title,
                body=content,
                representation='storage'
            )
            if page and 'id' in page:
                page_url = f"{confluence.url}/pages/viewpage.action?pageId={page['id']}"
                print(f"Confluence page '{title}' created successfully!", file=sys.stderr)
                return {
                    "status": "success",
                    "message": f"Confluence page created successfully",
                    "url": page_url
                }
            else:
                raise Exception("Failed to create page - no page ID returned!")
        except Exception as e:
            error_msg = f"Erro creating Confluence page: {str(e)}"
            print(error_msg, file=sys.stderr)
            traceback.print_exc(file=sys.stderr)
            return {"status": "error", "error": error_msg}