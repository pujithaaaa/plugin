---
name: github-info
description: Look up information about a GitHub repository — stars, forks, description, open issues, language, and default branch. Use when the user asks about a GitHub repo's stats or basic info.
---

# GitHub Repo Info

This skill answers questions about a GitHub repository's basic public info:
star count, fork count, description, open issue count, primary language,
and default branch.

## When to use this

Trigger this when the user asks things like:
- "What's the star count on X repo?"
- "Give me info about github.com/owner/repo"
- "How many open issues does X have?"

## Reference implementation

The following Python code (using PyGithub) is the working reference for
this capability, callable via a `GITHUB_TOKEN` environment variable in an
external runtime:

```python
from github import Github, Auth

def get_repo_info(repo: str, token: str) -> dict:
    client = Github(auth=Auth.Token(token))
    r = client.get_repo(repo)
    return {
        "name": r.full_name,
        "description": r.description,
        "stars": r.stargazers_count,
        "forks": r.forks_count,
        "open_issues": r.open_issues_count,
        "language": r.language,
        "default_branch": r.default_branch,
        "url": r.html_url,
    }
```

Note: this reference implementation requires network access and a GitHub
token, which are not available in this environment's execution sandbox.
