"""GitHub repo analysis service."""
import json
import logging
import requests
from typing import List, Dict
from backend.services.ai_service import ai_service
from backend.config import settings

logger = logging.getLogger(__name__)


class GitHubService:

    def fetch_repos(self, username: str, max_repos: int = 10) -> List[Dict]:
        """Fetch public repos from GitHub API."""
        headers = {}
        if settings.GITHUB_TOKEN:
            headers["Authorization"] = f"token {settings.GITHUB_TOKEN}"
        try:
            resp = requests.get(
                f"https://api.github.com/users/{username}/repos",
                params={"sort": "updated", "per_page": max_repos, "type": "owner"},
                headers=headers,
                timeout=10,
            )
            resp.raise_for_status()
            repos = resp.json()
            return [
                {
                    "name": r["name"],
                    "description": r.get("description") or "No description",
                    "language": r.get("language") or "Unknown",
                    "stars": r.get("stargazers_count", 0),
                    "forks": r.get("forks_count", 0),
                    "topics": r.get("topics", []),
                    "url": r.get("html_url", ""),
                    "updated_at": r.get("updated_at", ""),
                }
                for r in repos if not r.get("fork")
            ]
        except Exception as e:
            logger.error(f"GitHub API error: {e}")
            return []

    def analyze(self, username: str, max_repos: int = 10) -> dict:
        """Fetch repos and generate resume-ready bullet points."""
        repos = self.fetch_repos(username, max_repos)
        if not repos:
            return {"error": "No repos found or GitHub API error", "repos": [], "resume_points": [], "tech_stack": []}
        repos_text = json.dumps(repos, indent=2)
        analysis = ai_service.analyze_github(repos_text)
        if isinstance(analysis, dict):
            analysis["repos"] = repos
        return analysis


github_service = GitHubService()
