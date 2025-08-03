import os
import sys
import traceback
from dotenv import load_dotenv
from notion_client import Client as NotionClient
from atlassian import Confluence

class AuthError(Exception):
    pass

def load_env():
    load_dotenv()

def get_notion_client():
    api_key = os.getenv("NOTION_API_KEY")
    page_id = os.getenv("NOTION_PAGE_ID")
    if not api_key or not page_id:
        raise AuthError("Notion API key and page ID are required")
    notion = NotionClient(auth=api_key)
    return notion, page_id

def get_confluence_client():
    url = os.getenv("CONFLUENCE_URL")
    username = os.getenv("CONFLUENCE_USERNAME")
    api_token = os.getenv("CONFLUENCE_API_TOKEN")
    space_key = os.getenv("CONFLUENCE_SPACE_KEY")
    if not all([url, username, api_token, space_key]):
        raise AuthError("Missing Confluence credentials in environment variables")
    confluence = Confluence(
        url=url,
        username=username,
        password=api_token
    )
    return confluence, space_key

def get_github_headers():
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        raise AuthError("Missing Github token in environment variables")
    return {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json"
    }