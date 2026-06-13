"""CLI entry point for ai_gitgen."""

from __future__ import annotations

import argparse
import dataclasses
import sys
from collections.abc import Callable

from ai_gitgen import ai_client, git_io, prompts, render

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS_COMMIT = 400
DEFAULT_MAX_TOKENS_PR = 700
DIFF_CHAR_LIMIT = 8000

EXIT_OK = 0
EXIT_USAGE = 2
EXIT_GIT = 3
EXIT_AI = 4
EXIT_ENV = 5


def _add_shared_options(
    subparser: argparse.ArgumentParser, *, default_max_tokens: int
) -> None:
    subparser.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"AI model name (default: {DEFAULT_MODEL})",
    )
    subparser.add_argument(
        "--temperature",
        type=float,
        default=DEFAULT_TEMPERATURE,
        help=f"Sampling temperature (default: {DEFAULT_TEMPERATURE})",
    )
    subparser.add_argument(
        "--max-tokens",
        type=int,
        default=None,
        help=f"Maximum tokens in response (default: {default_max_tokens})",
    )
    subparser.add_argument(
        "--safe-mode",
        action="store_true",
        help="Mask obvious secrets in diff before sending to API",
    )


def _ai_exit_code(exc: ai_client.AIError) -> int:
    if "environment variable is not set" in str(exc):
        return EXIT_ENV
    return EXIT_AI


def _run_subcommand(
    args: argparse.Namespace,
    *,
    build_fn: Callable[..., list[dict[str, str]]],
    default_max_tokens: int,
) -> int:
    try:
        snapshot = git_io.collect()
    except git_io.GitError as exc:
        render.error(str(exc))
        return EXIT_GIT
    if snapshot.empty:
        render.no_changes()
        return EXIT_OK
    truncated_diff, was_truncated = git_io.truncate(snapshot.diff, DIFF_CHAR_LIMIT)
    snapshot_for_prompt = dataclasses.replace(snapshot, diff=truncated_diff)
    messages = build_fn(snapshot_for_prompt, truncated=was_truncated)
    try:
        text = ai_client.complete(
            messages,
            model=args.model,
            temperature=args.temperature,
            max_tokens=args.max_tokens or default_max_tokens,
        )
    except ai_client.AIError as exc:
        render.error(str(exc))
        return _ai_exit_code(exc)
    sys.stdout.write(text.rstrip() + "\n")
    return EXIT_OK


def _handle_commit(args: argparse.Namespace) -> int:
    return _run_subcommand(
        args,
        build_fn=prompts.build_commit,
        default_max_tokens=DEFAULT_MAX_TOKENS_COMMIT,
    )


def _handle_pr(args: argparse.Namespace) -> int:
    return _run_subcommand(
        args,
        build_fn=prompts.build_pr,
        default_max_tokens=DEFAULT_MAX_TOKENS_PR,
    )


def main(argv: list[str] | None = None) -> int:
    """Parse CLI arguments and dispatch to the appropriate subcommand handler."""
    parser = argparse.ArgumentParser(prog="ai_gitgen")
    subparsers = parser.add_subparsers(dest="command", required=True)

    commit_parser = subparsers.add_parser("commit", help="Generate a commit message")
    _add_shared_options(commit_parser, default_max_tokens=DEFAULT_MAX_TOKENS_COMMIT)
    commit_parser.set_defaults(handler=_handle_commit)

    pr_parser = subparsers.add_parser("pr", help="Generate a PR draft")
    _add_shared_options(pr_parser, default_max_tokens=DEFAULT_MAX_TOKENS_PR)
    pr_parser.set_defaults(handler=_handle_pr)

    args = parser.parse_args(argv)
    return args.handler(args)
