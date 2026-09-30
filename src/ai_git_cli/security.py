"""Mask sensitive values before Git context is sent to the AI API."""

import re

from .git_changes import GitSnapshot


MASKED_EMAIL = "[MASKED_EMAIL]"
MASKED_SECRET = "[MASKED_SECRET]"
MASKED_BEARER_TOKEN = "[MASKED_BEARER_TOKEN]"
MASKED_AWS_ACCESS_KEY = "[MASKED_AWS_ACCESS_KEY]"

_SECRET_NAME = r"[A-Za-z_][A-Za-z0-9_.-]*(?:api[_-]?key|token|secret|password|passwd)"
_QUOTED_ASSIGNMENT = re.compile(
    rf"""
    (?P<prefix>
        (?P<key_quote>["']?)
        {_SECRET_NAME}
        (?P=key_quote)
        \s*[:=]\s*
        (?P<value_quote>["'])
    )
    .*?
    (?P=value_quote)
    """,
    re.IGNORECASE | re.VERBOSE,
)
_UNQUOTED_ASSIGNMENT = re.compile(
    rf"""
    (?P<prefix>
        (?P<key_quote>["']?)
        {_SECRET_NAME}
        (?P=key_quote)
        \s*[:=]\s*
    )
    (?!["'])
    [^\s,;\#]+
    """,
    re.IGNORECASE | re.VERBOSE,
)
_BEARER_TOKEN = re.compile(
    r"(?i)\bBearer(?P<space>\s+)[^\s,;\"']+"
)
_AWS_ACCESS_KEY = re.compile(
    r"(?<![A-Z0-9])(?:AKIA|ASIA)[A-Z0-9]{16}(?![A-Z0-9])"
)
_EMAIL = re.compile(
    r"(?<![\w.+-])[\w.+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+(?![\w.-])"
)


def mask_text(text: str) -> tuple[str, int]:
    """Return masked text and the number of replaced sensitive values."""

    masked, quoted_count = _QUOTED_ASSIGNMENT.subn(
        lambda match: (
            f"{match.group('prefix')}{MASKED_SECRET}{match.group('value_quote')}"
        ),
        text,
    )
    masked, unquoted_count = _UNQUOTED_ASSIGNMENT.subn(
        lambda match: f"{match.group('prefix')}{MASKED_SECRET}", masked
    )
    masked, bearer_count = _BEARER_TOKEN.subn(
        lambda match: f"Bearer{match.group('space')}{MASKED_BEARER_TOKEN}", masked
    )
    masked, aws_count = _AWS_ACCESS_KEY.subn(MASKED_AWS_ACCESS_KEY, masked)
    masked, email_count = _EMAIL.subn(MASKED_EMAIL, masked)
    count = quoted_count + unquoted_count + bearer_count + aws_count + email_count
    return masked, count


def mask_snapshot(snapshot: GitSnapshot) -> tuple[GitSnapshot, int]:
    """Mask every prompt-context entry whose name ends with ``diff``."""

    context = dict(snapshot.prompt_context)
    count = 0
    for name, value in context.items():
        if name.casefold().endswith("diff"):
            context[name], masked_count = mask_text(value)
            count += masked_count
    return GitSnapshot(snapshot.status, snapshot.files, context), count
