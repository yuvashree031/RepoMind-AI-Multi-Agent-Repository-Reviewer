import os
import requests
from typing import Optional
from fastmcp import FastMCP

mcp = FastMCP("RepoMindAI")

API_URL = os.getenv("REPOMIND_API_URL", "http://localhost:8000")

@mcp.tool()
def list_analyzed_repositories() -> str:
    """
    Fetches the list of all repositories analyzed by RepoMind AI
    including their status and overall quality scores.
    """
    try:
        response = requests.get(f"{API_URL}/api/reviews", timeout=5)
        if response.status_code == 200:
            import json
            return json.dumps(response.json(), indent=2)
        return f"Error: Received status code {response.status_code} from backend."
    except Exception as e:
        return f"Failed to connect to backend: {str(e)}. Ensure FastAPI backend is running at {API_URL}."

@mcp.tool()
def get_repository_review_details(review_id: int) -> str:
    """
    Retrieves the complete findings and scores (Security, Code Quality, DevOps, Architecture)
    for a specific review session ID.
    """
    try:
        response = requests.get(f"{API_URL}/api/reviews/{review_id}", timeout=5)
        if response.status_code == 200:
            import json
            return json.dumps(response.json(), indent=2)
        return f"Error: Received status code {response.status_code} from backend."
    except Exception as e:
        return f"Failed to connect to backend: {str(e)}. Ensure FastAPI backend is running at {API_URL}."

@mcp.tool()
def queue_repository_audit(repo_url: str, git_token: Optional[str] = None) -> str:
    """
    Queues a new GitHub repository for automated auditing.
    Cloning, code parsing, and AI agent checks will run asynchronously.
    """
    try:
        payload = {"url": repo_url}
        if git_token:
            payload["token"] = git_token
            
        response = requests.post(f"{API_URL}/api/analyze", json=payload, timeout=10)
        if response.status_code in (200, 201):
            import json
            return json.dumps(response.json(), indent=2)
        return f"Error: Backend returned {response.status_code} - {response.text}"
    except Exception as e:
        return f"Failed to submit audit to backend: {str(e)}. Ensure FastAPI backend is running."
