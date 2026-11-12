"""Create a triage issue, and optionally a pull request summary, from a change set.

Invoked by ``.github/workflows/ai-issue.yml`` for pushes to the default branch and
for pull requests. The module collects the change set, selects a review persona
from the trigger labels (falling back to content heuristics), asks a hosted model
for a structured report, and publishes that report as a GitHub issue.

The script is best-effort by contract: it runs as repository housekeeping, so any
recoverable failure (model outage, malformed reply, duplicate issue) ends the run
with a message instead of failing the workflow. Configuration errors are the
exception and abort immediately with a non-zero status.

Environment:
    GITHUB_TOKEN: Token used for the GitHub API (provided by Actions).
    GH_MODELS_TOKEN: Bearer token for the hosted inference endpoint.
    REPOSITORY: Target repository in ``owner/name`` form.
    EVENT_NAME: ``push`` or ``pull_request``.
    COMMIT_SHA: Head commit of the event; used for permalinks.
    PR_NUMBER: Pull request number; required for ``pull_request`` events.
    ALLOWED_USER: Comma-separated logins permitted to trigger the script.
    GITHUB_ACTOR: Login of the actor that triggered the run.
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
from dataclasses import dataclass
from typing import Final, Iterable, Mapping
from urllib.parse import quote

import requests
from github import Auth, Github, GithubException
from github.Commit import Commit
from github.PullRequest import PullRequest
from github.Repository import Repository

MODEL_NAME: Final = "Llama-3.3-70B-Instruct"
MODEL_ENDPOINT: Final = "https://models.inference.ai.azure.com/chat/completions"
REQUEST_TIMEOUT_SECONDS: Final = 60
MODEL_ATTEMPTS: Final = 3
RETRY_DELAY_SECONDS: Final = 5

#: Diff budget per event type, in characters. Pushes cover a single commit and
#: stay small; pull requests can legitimately carry a much larger change set.
DIFF_LIMIT_PUSH: Final = 10_000
DIFF_LIMIT_PULL_REQUEST: Final = 80_000

#: A change set shorter than this carries no reviewable information.
MIN_DIFF_CHARS: Final = 50

#: Placeholder the model is asked to emit so the script can substitute a
#: permalink once the head commit is known.
PERMALINK_PLACEHOLDER: Final = "PUT_PERMALINK_HERE"

_CODE_FENCE_PATTERN = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)
_PR_REFERENCE_PATTERN = re.compile(r"\(#(\d+)\)")
_BRACKET_LABEL_PATTERN = re.compile(r"\[(.*?)\]")

SEVERITY_GUIDE = """\
Use the following severity scale. You have 7 levels -- pick the one that best \
matches the ACTUAL impact:

CRITICAL -- Production-breaking changes, security vulnerabilities (exposed \
secrets, SQL injection, XSS, CSRF, broken auth), data loss risks, or changes that \
could cause service outages.

HIGH -- Significant logic changes affecting core functionality, new or modified \
API endpoints, permission and access control modifications, database schema \
changes, removal of important functionality, breaking changes to public interfaces.

ELEVATED -- New substantial features or modules, large-scale refactors that change \
behavior across multiple files, integration with external services or APIs, changes \
to error handling or retry logic, modifications to data processing pipelines.

MEDIUM -- New utility functions or helpers, workflow and CI/CD pipeline changes, \
configuration changes that affect runtime behavior, dependency version updates, \
adding new files with meaningful functionality, structural reorganization of \
existing code.

MODERATE -- Minor feature additions, small behavioral changes, adding validation or \
input checks, improving logging or error messages, updating environment variables or \
build settings, adding new labels or issue templates.

LOW -- Documentation updates (README, CONTRIBUTING, comments), cosmetic UI changes \
without behavior impact, code formatting or style fixes, renaming without behavior \
change, adding badges or metadata, updating .gitignore or editor configs.

INFORMATIONAL -- Trivial changes: fixing typos, whitespace adjustments, comment \
rewording, version bumps in non-critical files, adding blank lines.

IMPORTANT: Do NOT default to LOW or INFORMATIONAL. Carefully evaluate the actual \
scope and impact. Most code changes that add or modify functionality should be \
MEDIUM or higher. Use the full range of the scale.
"""

OUTPUT_CONTRACT = """\
Return only a raw JSON object with no markdown formatting. The JSON must have \
these exact keys:

"issue_title": string -- include a severity prefix like [CRITICAL], [HIGH], \
[ELEVATED], [MEDIUM], [MODERATE], [LOW], or [INFO] at the start,
"severity": string -- one of: critical, high, elevated, medium, moderate, low, \
informational,
"issue_body": string -- must include these sections:
  ## Problem
  (clear description with exact file paths and line numbers if known)

  ## Code Reference
  (the exact problematic code snippet or the key changed code)

  ## Suggested Fix
  (concrete code or steps to fix -- or "No action required" for informational \
changes)

  ## Permalink
  (placeholder: PUT_PERMALINK_HERE -- will be replaced automatically)

"labels": list of strings -- standard GitHub labels plus the severity level,
"affected_file": string -- the most relevant filename from the diff (or "" if \
unknown),
"affected_line": integer -- approximate line number of the issue (or 1 if unknown),
"summary": string -- 2-3 sentence plain-English summary for the pull request comment

The issue_title, issue_body and summary MUST be written entirely in English.
"""

#: Review personas keyed by role. The label map below resolves user labels onto
#: these keys; ``general`` is the fallback persona.
PROMPT_ROLES: Final[Mapping[str, str]] = {
    "security": (
        "Act as a Strict Security Auditor. Perform a deep security audit "
        "(OWASP Top 10, CWE patterns). Find real vulnerabilities with exact "
        "file/line references. Check for exposed secrets, injection vectors, "
        "broken auth, insecure deserialization, and misconfigurations."
    ),
    "review": (
        "Act as a Strict Code Reviewer. Analyze code quality using SOLID, DRY, "
        "and KISS principles. Point to exact lines that violate these principles. "
        "Evaluate naming, error handling, and separation of concerns."
    ),
    "qa": (
        "Act as a QA Engineer. Identify edge cases, missing test coverage, "
        "untested error paths, and potential regressions. Reference exact "
        "functions and lines that need tests."
    ),
    "perf": (
        "Act as a Performance Expert. Analyze algorithmic complexity, identify "
        "O(n^2) patterns, unnecessary allocations, N+1 queries, blocking I/O, "
        "and missed caching opportunities. Reference exact lines."
    ),
    "pm": (
        "Act as a Product Manager. Generate user-facing Release Notes with "
        "clear impact descriptions. Focus on what changed for the end user, "
        "not implementation details."
    ),
    "deps": (
        "Act as a Security & Dependency Auditor. Analyze all new or changed "
        "dependencies: check for known vulnerabilities (CVEs), license "
        "compatibility (MIT/Apache/GPL), package size impact, maintenance "
        "status, and whether each dep is actively maintained. Reference exact "
        "file and line where each dependency is added or changed."
    ),
    "arch": (
        "Act as a Software Architect. Review changes for architectural issues: "
        "violation of separation of concerns, tight coupling, wrong layer "
        "dependencies, anti-patterns (God object, spaghetti logic, magic "
        "numbers, circular dependencies). Reference exact files and lines."
    ),
    "ci": (
        "Act as a DevOps/CI Engineer. Review the CI/CD pipeline changes for "
        "correctness, security (token permissions, secret exposure), efficiency "
        "(caching, parallelism, job dependencies), and best practices. Check "
        "for overly broad permissions, missing timeout limits, and potential "
        "race conditions in workflows."
    ),
    "docs": (
        "Act as a Technical Writer. Review the documentation changes for "
        "completeness, accuracy, clarity, and consistency. Check that code "
        "examples are correct, links are valid, and the structure is logical. "
        "Note any missing sections or outdated information."
    ),
    "frontend": (
        "Act as a Frontend Engineer. Review the UI/UX changes for accessibility "
        "(a11y), responsive design, performance (bundle size, render blocking), "
        "XSS risks in DOM manipulation, proper event handling, and browser "
        "compatibility. Reference exact files and lines."
    ),
    "backend": (
        "Act as a Senior Backend Engineer. Review the changes for correctness, "
        "error handling, input validation, resource management (file handles, "
        "connections), concurrency safety, and API contract compliance. "
        "Reference exact files and lines."
    ),
    "config": (
        "Act as a Configuration & Infrastructure Reviewer. Analyze the config "
        "changes for correctness, security implications (exposed ports, "
        "permissive CORS, debug mode in production), consistency across "
        "environments, and potential breaking changes for existing deployments."
    ),
    "general": (
        "Act as a Senior Software Engineer reviewing a colleague's changes. "
        "Provide a thorough assessment covering: what was changed and why, "
        "whether the changes introduce any risks or bugs, code quality, "
        "and the overall scope and impact on the project."
    ),
}

#: Maps commit-message brackets and pull request labels onto role keys.
LABEL_TO_ROLE: Final[Mapping[str, str]] = {
    "sec": "security", "security": "security", "audit": "security",
    "review": "review", "refactor": "review", "code-review": "review",
    "qa": "qa", "test": "qa", "testing": "qa",
    "perf": "perf", "performance": "perf", "optimize": "perf",
    "pm": "pm", "release": "pm", "product": "pm",
    "deps": "deps", "dependencies": "deps", "dep": "deps",
    "arch": "arch", "architecture": "arch",
    "ci": "ci", "devops": "ci", "pipeline": "ci", "workflow": "ci",
    "docs": "docs", "doc": "docs", "documentation": "docs",
    "frontend": "frontend", "ui": "frontend", "ux": "frontend", "css": "frontend",
    "backend": "backend", "api": "backend", "server": "backend",
    "config": "config", "infra": "config", "infrastructure": "config",
}

SEVERITY_LABELS: Final[Mapping[str, str]] = {
    "critical": "severity: critical",
    "high": "severity: high",
    "elevated": "severity: elevated",
    "medium": "severity: medium",
    "moderate": "severity: moderate",
    "low": "severity: low",
    "informational": "severity: informational",
}

#: File-name and content markers used to infer the review persona when the
#: change set carries no recognisable label.
_CHANGE_CLASSIFIERS: Final = (
    (
        "security",
        (
            "secret", "token", "password", "api_key", "apikey", "auth",
            "credential", "private_key", "access_key", "bearer",
            "vulnerability", "cve-", "injection", "xss", "csrf",
        ),
        ("security", "auth", ".env", "secret"),
    ),
    (
        "deps",
        (),
        (
            "requirements", "package.json", "package-lock", "pipfile",
            "poetry.lock", "cargo.toml", "go.sum", "gemfile",
            "dependabot", "renovate",
        ),
    ),
    (
        "ci",
        (),
        (
            ".github/workflows/", "jenkinsfile", ".gitlab-ci",
            ".circleci", "dockerfile", "docker-compose", ".github/actions/",
        ),
    ),
    (
        "frontend",
        ("classname", "style=", "onclick", "addeventlistener", "document.get", "innerhtml", "appendchild"),
        (".html", ".css", ".jsx", ".tsx", ".vue", ".svelte", "frontend/", "public/", "static/", "assets/"),
    ),
    (
        "backend",
        (),
        (".py", ".go", ".java", ".rb", ".rs", ".php", "api/", "server/", "backend/", "lib/", "src/"),
    ),
    (
        "config",
        (),
        (".yml", ".yaml", ".toml", ".ini", ".cfg", ".conf", ".json", ".env"),
    ),
)

_DOCUMENTATION_MARKERS: Final = (
    "readme", "contributing", "changelog", "license", "docs/", "doc/", ".md", ".rst", ".txt",
)


@dataclass(frozen=True)
class Settings:
    """Runtime configuration resolved from the environment."""

    github_token: str
    models_token: str
    repository: str
    event_name: str
    commit_sha: str
    pull_number: int | None
    allowed_users: frozenset[str]
    actor: str

    @classmethod
    def from_environment(cls) -> "Settings":
        event_name = _require_env("EVENT_NAME")
        pull_number = os.environ.get("PR_NUMBER", "").strip()

        return cls(
            github_token=_require_env("GITHUB_TOKEN"),
            models_token=_require_env("GH_MODELS_TOKEN"),
            repository=_require_env("REPOSITORY"),
            event_name=event_name,
            commit_sha=os.environ.get("COMMIT_SHA", "").strip(),
            pull_number=int(pull_number) if pull_number else None,
            allowed_users=_parse_logins(os.environ.get("ALLOWED_USER", "")),
            actor=os.environ.get("GITHUB_ACTOR", "").strip().lower(),
        )


@dataclass(frozen=True)
class ChangeSet:
    """Everything the review needs to know about the triggering change."""

    diff: str
    changed_files: tuple[str, ...]
    context: str
    labels: tuple[str, ...]
    dedup_key: str


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


def _accumulate_diff(changes: Iterable[tuple[str, str | None]], limit: int) -> tuple[str, tuple[str, ...]]:
    """Flatten ``(filename, patch)`` pairs into a prompt fragment.

    Files without a textual patch (binary assets, pure renames) are annotated
    instead of being rendered as ``None``, and the accumulation stops at ``limit``
    characters so a large change set cannot exhaust the model context.
    """
    fragments: list[str] = []
    filenames: list[str] = []
    total = 0

    for filename, patch in changes:
        filenames.append(filename)
        fragment = f"File: {filename}\nPatch:\n{patch or '[no textual diff available]'}\n\n"
        fragments.append(fragment)
        total += len(fragment)

        if total >= limit:
            fragments.append("[Diff truncated: size limit reached.]\n")
            break

    return "".join(fragments), tuple(filenames)


def collect_push_change_set(repository: Repository, settings: Settings) -> ChangeSet | None:
    """Build the change set for a push event, or ``None`` when not allow-listed."""
    if settings.actor not in settings.allowed_users:
        print(f"Actor {settings.actor!r} is not allow-listed; skipping.")
        return None

    commit: Commit = repository.get_commit(settings.commit_sha)
    message = commit.commit.message

    reference = _PR_REFERENCE_PATTERN.search(message)
    dedup_key = f"PR #{reference.group(1)}" if reference else f"commit:{settings.commit_sha[:7]}"

    diff, files = _accumulate_diff(
        ((item.filename, item.patch) for item in commit.files),
        DIFF_LIMIT_PUSH,
    )

    return ChangeSet(
        diff=diff,
        changed_files=files,
        context=f"Commit Message: {message}",
        labels=tuple(match.lower() for match in _BRACKET_LABEL_PATTERN.findall(message)),
        dedup_key=dedup_key,
    )


def collect_pull_request_change_set(repository: Repository, settings: Settings) -> tuple[ChangeSet | None, PullRequest | None]:
    """Build the change set for a pull request event.

    Returns the change set together with the pull request handle, which is reused
    later to post the summary comment. Both are ``None`` when the author is not
    allow-listed.
    """
    if settings.pull_number is None:
        raise SystemExit("PR_NUMBER is required for pull_request events.")

    pull = repository.get_pull(settings.pull_number)
    author = pull.user.login.strip().lower()

    if author not in settings.allowed_users:
        print(f"Pull request author {author!r} is not allow-listed; skipping.")
        return None, None

    diff, files = _accumulate_diff(
        ((item.filename, item.patch) for item in pull.get_files()),
        DIFF_LIMIT_PULL_REQUEST,
    )

    change_set = ChangeSet(
        diff=diff,
        changed_files=files,
        context=f"PR Title: {pull.title}\nPR Body: {pull.body or ''}",
        labels=tuple(label.name.lower() for label in pull.labels),
        dedup_key=f"PR #{settings.pull_number}",
    )
    return change_set, pull


def detect_change_type(files: Iterable[str], diff: str) -> str:
    """Infer the review persona from changed paths and diff content.

    Labels always win over inference; this is the fallback for change sets that
    arrive without one. Documentation-only change sets are recognised first
    because a docs patch frequently also touches ``.json`` or ``.py`` paths.
    """
    lowered_files = [name.lower() for name in files]
    lowered_diff = diff.lower()

    if lowered_files and all(
        any(marker in name for marker in _DOCUMENTATION_MARKERS) for name in lowered_files
    ):
        return "docs"

    for role, content_markers, file_markers in _CHANGE_CLASSIFIERS:
        if any(marker in lowered_diff for marker in content_markers):
            return role
        if any(marker in name for name in lowered_files for marker in file_markers):
            return role

    return "general"


def select_role(labels: Iterable[str], files: Iterable[str], diff: str) -> str:
    """Resolve the review persona from the first recognised label, else heuristics."""
    for label in labels:
        role = LABEL_TO_ROLE.get(label.strip().lower())
        if role is not None:
            return role

    detected = detect_change_type(files, diff)
    print(f"Auto-detected change type: {detected}")
    return detected


def build_prompt(role: str, change_set: ChangeSet) -> str:
    """Assemble the review prompt for a persona and a change set."""
    return (
        f"{PROMPT_ROLES[role]}\n\n"
        "Do NOT invent problems that do not exist in the diff. "
        "Base your analysis strictly on what you see.\n"
        f"{SEVERITY_GUIDE}\n"
        f"Context: {change_set.context}\n"
        f"Changed files: {', '.join(change_set.changed_files)}\n"
        f"Changes: {change_set.diff}\n"
        f"{OUTPUT_CONTRACT}"
    )


def call_model(prompt: str, token: str, attempts: int = MODEL_ATTEMPTS) -> dict | None:
    """Request the structured report, retrying transient failures.

    Returns ``None`` once the retry budget is exhausted so the caller can exit
    cleanly; a malformed reply is treated the same way as a transport error.
    """
    payload = {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are a professional software auditor. Always return valid JSON only. "
                    "No markdown, no explanation, just the JSON object."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "model": MODEL_NAME,
        "temperature": 0.1,
    }
    headers = {"Content-Type": "application/json", "Authorization": f"Bearer {token}"}

    for attempt in range(1, attempts + 1):
        try:
            response = requests.post(MODEL_ENDPOINT, headers=headers, json=payload, timeout=REQUEST_TIMEOUT_SECONDS)
            response.raise_for_status()
            raw = response.json()["choices"][0]["message"]["content"].strip()
            return json.loads(_CODE_FENCE_PATTERN.sub("", raw))
        except (requests.RequestException, KeyError, IndexError, ValueError) as error:
            print(f"Attempt {attempt}/{attempts} failed: {error}")
            if attempt < attempts:
                # Linear backoff: enough to ride out a transient upstream hiccup
                # without keeping the job alive for long.
                time.sleep(RETRY_DELAY_SECONDS * attempt)

    return None


def find_existing_issue(repository: Repository, dedup_key: str) -> int | None:
    """Return the number of an issue already documenting ``dedup_key``."""
    for issue in repository.get_issues(state="all"):
        if dedup_key in (issue.body or ""):
            return issue.number
    return None


def find_closed_issue_by_title(repository: Repository, title_keyword: str) -> int | None:
    """Return the number of a closed issue whose title contains ``title_keyword``."""
    if not title_keyword:
        return None

    for issue in repository.get_issues(state="closed"):
        if title_keyword.lower() in (issue.title or "").lower():
            return issue.number
    return None


def _as_line_number(value: object) -> int:
    """Coerce the model-reported line number to a positive integer, else 1."""
    try:
        line = int(float(str(value).strip()))
    except (TypeError, ValueError):
        return 1
    return line if line > 0 else 1


def build_permalink(repository_name: str, commit_sha: str, filename: str, line: object) -> str:
    """Build a GitHub blob permalink for a file and line.

    The filename and line originate from the model's reply, so both are
    sanitised before being embedded in a URL: a path is percent-encoded and the
    line is coerced to a positive integer.
    """
    safe_path = quote(filename.strip().lstrip("/"), safe="/")
    return f"https://github.com/{repository_name}/blob/{commit_sha}/{safe_path}#L{_as_line_number(line)}"


def publish_report(
    repository: Repository,
    report: Mapping,
    change_set: ChangeSet,
    settings: Settings,
    role: str,
    pull: PullRequest | None,
) -> int:
    """Create the triage issue, then optionally post the PR summary comment.

    Returns the created issue number.
    """
    affected_file = str(report.get("affected_file") or "").strip()
    affected_line = _as_line_number(report.get("affected_line"))
    permalink = (
        build_permalink(settings.repository, settings.commit_sha, affected_file, affected_line)
        if affected_file and settings.commit_sha
        else "_No specific file identified_"
    )

    issue_body = str(report.get("issue_body", "")).replace(PERMALINK_PLACEHOLDER, permalink)
    severity = str(report.get("severity", "medium")).lower()
    severity_label = SEVERITY_LABELS.get(severity, SEVERITY_LABELS["medium"])

    requested_labels = [str(label) for label in report.get("labels") or []]
    footer = (
        f"\n\n---\n*Generated from {change_set.dedup_key} | "
        f"Auto-detected role: `{role}` | Processed by actor: {settings.actor or 'unknown'}*"
    )

    issue = repository.create_issue(
        title=str(report.get("issue_title", "")).strip() or f"Triage report for {change_set.dedup_key}",
        body=issue_body + footer,
        labels=sorted({*requested_labels, severity_label}),
    )
    print(f"Created issue #{issue.number}: {issue.title}")

    summary = str(report.get("summary", "")).strip()
    if pull is not None and summary:
        pull.create_issue_comment(
            f"### AI Analysis Summary\n\n"
            f"{summary}\n\n"
            f"**Severity:** `{severity.upper()}` | **Role:** `{role}`\n\n"
            f"Full details: #{issue.number}"
        )
        print(f"Posted summary comment to PR #{pull.number}")

    return issue.number


def main() -> int:
    settings = Settings.from_environment()

    if settings.event_name not in {"push", "pull_request"}:
        print(f"Event {settings.event_name!r} is not handled; skipping.")
        return 0

    github = Github(auth=Auth.Token(settings.github_token))
    repository = github.get_repo(settings.repository)

    if settings.event_name == "push" and not settings.commit_sha:
        raise SystemExit("COMMIT_SHA is required for push events.")

    pull: PullRequest | None = None
    if settings.event_name == "push":
        change_set = collect_push_change_set(repository, settings)
    else:
        change_set, pull = collect_pull_request_change_set(repository, settings)

    if change_set is None:
        return 0

    if len(change_set.diff.strip()) < MIN_DIFF_CHARS:
        print("Diff too small to analyze; skipping.")
        return 0

    existing_issue = find_existing_issue(repository, change_set.dedup_key)
    if existing_issue is not None:
        print(f"Issue for {change_set.dedup_key} already exists (#{existing_issue}); skipping.")
        return 0

    role = select_role(change_set.labels, change_set.changed_files, change_set.diff)
    report = call_model(build_prompt(role, change_set), settings.models_token)

    if report is None:
        print("The model produced no usable report; skipping.")
        return 0

    closed_match = find_closed_issue_by_title(repository, str(report.get("issue_title", ""))[:40])
    if closed_match is not None:
        print(f"Similar closed issue found (#{closed_match}); skipping.")
        return 0

    try:
        publish_report(repository, report, change_set, settings, role, pull)
    except GithubException as error:
        print(f"Failed to publish the report: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
