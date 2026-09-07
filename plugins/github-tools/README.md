# GitHub Plugin

Gives a Claude-wrapped agent 5 GitHub functions: get repo info, create an
issue, list recent commits, check PR status, and create a pull request.

## 1. Create a Personal Access Token (PAT)

1. Go to https://github.com/settings/tokens?type=beta (fine-grained tokens,
   recommended) or https://github.com/settings/tokens (classic).
2. **Fine-grained token:** pick the repo(s) it can access, then under
   **Repository permissions** grant:
   - `Contents`: Read
   - `Issues`: Read and write
   - `Pull requests`: Read and write
   - `Metadata`: Read (usually auto-included)
3. **Classic token:** just check the `repo` scope box (simpler, but broader
   access — grants access to all your repos).
4. Generate the token and copy it (starts with `github_pat_` for
   fine-grained, or `ghp_` for classic). GitHub only shows it once.

## 2. Set the token

```bash
export GITHUB_TOKEN=github_pat_your-token-here
```

Don't hardcode this — same rule as the Slack token, it needs to stay out of
your repo and commit history.

## 3. Install and run

```bash
pip install -r requirements.txt
python -c "
from github_tools import GitHubPlugin
plugin = GitHubPlugin()
print(plugin.dispatch('get_repo_info', {'repo': 'your-username/your-repo'}))
"
```

## 4. Wiring into your Coworker agent / Claude-wrapped agent

`GitHubPlugin.TOOL_SCHEMAS` is a list of Anthropic-format tool definitions —
pass it directly as the `tools` param in a Claude API call. When Claude
returns a `tool_use` block, call:

```python
result = plugin.dispatch(tool_use_block.name, tool_use_block.input)
```

and feed `result` back as the `tool_result`.

## Notes

- `repo` is always `"owner/repo-name"` format (e.g. `"pujitha/video-agent"`),
  not a URL.
- `create_pull_request`'s `head` branch must already exist and have commits
  ahead of `base`, or GitHub will reject the PR creation.
- `check_pr_status` without a `pr_number` lists all open PRs — useful for
  "what's pending" style prompts.
