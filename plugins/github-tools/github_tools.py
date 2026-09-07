"""
GitHub plugin for a Claude-wrapped agent.

Exposes 5 functions as Claude tools:
  - get_repo_info
  - create_issue
  - list_recent_commits
  - check_pr_status
  - create_pull_request

Usage:
    from github_tools import GitHubPlugin

    plugin = GitHubPlugin(token=os.environ["GITHUB_TOKEN"])
    result = plugin.dispatch("get_repo_info", {"repo": "owner/repo-name"})

    # To wire into Claude's tool-use API, pass GitHubPlugin.TOOL_SCHEMAS as your
    # `tools` list, and call plugin.dispatch(tool_name, tool_input) whenever
    # Claude returns a tool_use block.
"""

import os
from github import Github, Auth
from github.GithubException import GithubException


class GitHubPlugin:
    def __init__(self, token: str | None = None):
        auth = Auth.Token(token or os.environ["GITHUB_TOKEN"])
        self.client = Github(auth=auth)

    # ---------- the 5 functions ----------

    def get_repo_info(self, repo: str) -> dict:
        """repo format: 'owner/repo-name'"""
        r = self.client.get_repo(repo)
        return {
            "ok": True,
            "name": r.full_name,
            "description": r.description,
            "stars": r.stargazers_count,
            "forks": r.forks_count,
            "open_issues": r.open_issues_count,
            "language": r.language,
            "default_branch": r.default_branch,
            "url": r.html_url,
        }

    def create_issue(self, repo: str, title: str, body: str = "", labels: list[str] | None = None) -> dict:
        r = self.client.get_repo(repo)
        issue = r.create_issue(title=title, body=body, labels=labels or [])
        return {"ok": True, "number": issue.number, "url": issue.html_url}

    def list_recent_commits(self, repo: str, branch: str | None = None, count: int = 5) -> dict:
        r = self.client.get_repo(repo)
        commits = r.get_commits(sha=branch) if branch else r.get_commits()
        result = []
        for c in commits[:count]:
            result.append({
                "sha": c.sha[:7],
                "message": c.commit.message.split("\n")[0],
                "author": c.commit.author.name,
                "date": c.commit.author.date.isoformat(),
                "url": c.html_url,
            })
        return {"ok": True, "commits": result}

    def check_pr_status(self, repo: str, pr_number: int | None = None) -> dict:
        r = self.client.get_repo(repo)
        if pr_number is not None:
            pr = r.get_pull(pr_number)
            return {
                "ok": True,
                "number": pr.number,
                "title": pr.title,
                "state": pr.state,
                "merged": pr.merged,
                "mergeable": pr.mergeable,
                "checks_url": f"{pr.html_url}/checks",
                "url": pr.html_url,
            }
        # No number given: list open PRs
        prs = r.get_pulls(state="open")
        result = [{"number": p.number, "title": p.title, "url": p.html_url} for p in prs]
        return {"ok": True, "open_pull_requests": result}

    def create_pull_request(self, repo: str, title: str, head: str, base: str = "main", body: str = "") -> dict:
        r = self.client.get_repo(repo)
        pr = r.create_pull(title=title, body=body, head=head, base=base)
        return {"ok": True, "number": pr.number, "url": pr.html_url}

    # ---------- dispatcher ----------

    def dispatch(self, tool_name: str, tool_input: dict) -> dict:
        """Call one of the 5 functions by name with the given kwargs, catching GitHub API errors."""
        fn = getattr(self, tool_name, None)
        if fn is None:
            return {"ok": False, "error": f"Unknown tool: {tool_name}"}
        try:
            return fn(**tool_input)
        except GithubException as e:
            return {"ok": False, "error": e.data.get("message", str(e))}
        except ValueError as e:
            return {"ok": False, "error": str(e)}

    # ---------- Claude tool-use schemas ----------

    TOOL_SCHEMAS = [
        {
            "name": "get_repo_info",
            "description": "Get basic info about a GitHub repo: stars, forks, description, open issues, language.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo in 'owner/repo-name' format"},
                },
                "required": ["repo"],
            },
        },
        {
            "name": "create_issue",
            "description": "Create a new issue in a GitHub repo.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo in 'owner/repo-name' format"},
                    "title": {"type": "string", "description": "Issue title"},
                    "body": {"type": "string", "description": "Issue description/body"},
                    "labels": {"type": "array", "items": {"type": "string"}, "description": "Optional list of label names"},
                },
                "required": ["repo", "title"],
            },
        },
        {
            "name": "list_recent_commits",
            "description": "List the most recent commits on a GitHub repo or branch.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo in 'owner/repo-name' format"},
                    "branch": {"type": "string", "description": "Optional branch name; defaults to the repo's default branch"},
                    "count": {"type": "integer", "description": "Number of commits to return", "default": 5},
                },
                "required": ["repo"],
            },
        },
        {
            "name": "check_pr_status",
            "description": "Check the status of a specific pull request, or list all open pull requests if no number is given.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo in 'owner/repo-name' format"},
                    "pr_number": {"type": "integer", "description": "Optional PR number. Omit to list all open PRs instead."},
                },
                "required": ["repo"],
            },
        },
        {
            "name": "create_pull_request",
            "description": "Create a new pull request in a GitHub repo.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Repo in 'owner/repo-name' format"},
                    "title": {"type": "string", "description": "PR title"},
                    "head": {"type": "string", "description": "The branch with changes (source branch)"},
                    "base": {"type": "string", "description": "The branch to merge into (default: main)", "default": "main"},
                    "body": {"type": "string", "description": "PR description"},
                },
                "required": ["repo", "title", "head"],
            },
        },
    ]
