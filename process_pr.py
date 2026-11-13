"""Turn a labelled pull request into a documented GitHub issue.

Runs from ``.github/workflows/pr-to-issue.yml`` when a maintainer applies the
``auto-document`` label: the pull request diff is summarised by a hosted model and
the result is filed as an issue. Execution is best-effort by design -- the
workflow is an internal convenience, so an upstream model failure must not fail
the build.

Environment:
    GITHUB_TOKEN: Token used for the GitHub API (provided by Actions).
    GEMINI_API_KEY: API key for the Generative Language API.
    REPOSITORY: Target repository in ``owner/name`` form.
    PR_NUMBER: Pull request number to document.
    ALLOWED_USER: Comma-separated logins permitted to trigger the script.
"""

from __future__ import annotations

import json
import os
import re
import sys
from dataclasses import dataclass

import requests
from github import Auth, Github, GithubException
from github.PullRequest import PullRequest

MODEL_NAME = "gemini-2.5-flash"
MODEL_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

#: Upper bound for the diff sent to the model, in characters. Keeps the request
#: well inside the model's context window and bounds the cost per pull request.
MAX_DIFF_CHARS = 100_000
REQUEST_TIMEOUT_SECONDS = 60

_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)

PROMPT_TEMPLATE = """\
Analyze this pull request and write a description for a GitHub issue that \
explains what was implemented or fixed.
PR title: {title}
PR body: {body}

Code changes:
{diff}

Return only a raw JSON object with no markdown formatting. The JSON must contain \
exactly these keys:
"issue_title": string,
"issue_body": string
"""


@dataclass(frozen=True)
class Settings:
    """Runtime configuration resolved from the environment."""

    github_token: str
    gemini_api_key: str
    repository: str
    pull_number: int
    allowed_users: frozenset[str]

    @classmethod
    def from_environment(cls) -> "Settings":
        return cls(
            github_token=_require_env("GITHUB_TOKEN"),
            gemini_api_key=_require_env("GEMINI_API_KEY"),
            repository=_require_env("REPOSITORY"),
            pull_number=int(_require_env("PR_NUMBER")),
            allowed_users=_parse_logins(os.environ.get("ALLOWED_USER", "")),
        )


def _require_env(name: str) -> str:
    """Return a mandatory environment variable, or abort with a clear message."""
    value = os.environ.get(name, "").strip()
    if not value:
        raise SystemExit(f"Required environment variable {name} is not set.")
    return value


def _parse_logins(raw: str) -> frozenset[str]:
    """Normalise a comma-separated login list to a case-insensitive set."""
    logins = (item.strip().lower() for item in raw.split(","))
    return frozenset(login for login in logins if login)


def collect_diff(pull: PullRequest, limit: int = MAX_DIFF_CHARS) -> str:
    """Flatten the pull request's file patches into a single prompt fragment.

    Binary and renamed files report ``patch`` as ``None``; those are represented
    by a placeholder rather than the string ``"None"`` so the model can tell the
    difference between an absent patch and a real one.
    """
    fragments: list[str] = []
    total = 0

    for changed_file in pull.get_files():
        patch = changed_file.patch or "[no textual diff available]"
        fragment = f"File: {changed_file.filename}\nPatch:\n{patch}\n\n"
        fragments.append(fragment)
        total += len(fragment)

        if total >= limit:
            fragments.append("[Diff truncated: size limit reached.]\n")
            break

    return "".join(fragments)


def request_issue_draft(settings: Settings, prompt: str) -> dict[str, str]:
    """Ask the hosted model for the issue draft and parse its JSON reply."""
    response = requests.post(
        MODEL_ENDPOINT.format(model=MODEL_NAME),
        params={"key": settings.gemini_api_key},
        json={"contents": [{"parts": [{"text": prompt}]}]},
        headers={"Content-Type": "application/json"},
        timeout=REQUEST_TIMEOUT_SECONDS,
    )
    response.raise_for_status()

    candidates = response.json().get("candidates") or []
    if not candidates:
        raise ValueError("The model returned no candidates.")

    text = candidates[0]["content"]["parts"][0]["text"].strip()
    # Models occasionally wrap JSON in a Markdown fence despite the instruction.
    draft = json.loads(_FENCE_PATTERN.sub("", text))

    for key in ("issue_title", "issue_body"):
        if not isinstance(draft.get(key), str) or not draft[key].strip():
            raise ValueError(f"The model response is missing a usable '{key}'.")

    return draft


def main() -> int:
    settings = Settings.from_environment()

    github = Github(auth=Auth.Token(settings.github_token))
    repository = github.get_repo(settings.repository)
    pull = repository.get_pull(settings.pull_number)

    if pull.user.login.strip().lower() not in settings.allowed_users:
        print(f"Pull request author {pull.user.login!r} is not allow-listed; skipping.")
        return 0

    prompt = PROMPT_TEMPLATE.format(
        title=pull.title,
        body=pull.body or "",
        diff=collect_diff(pull),
    )

    try:
        draft = request_issue_draft(settings, prompt)
        issue_body = f"{draft['issue_body'].strip()}\n\n---\n*Generated from PR #{settings.pull_number}.*"
        issue = repository.create_issue(title=draft["issue_title"].strip(), body=issue_body)
    except (requests.RequestException, GithubException, ValueError, KeyError) as error:
        # The workflow is housekeeping: report the failure and leave the build green.
        print(f"Unable to document the pull request: {error}", file=sys.stderr)
        return 1

    print(f"Created issue #{issue.number}: {issue.title}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
