"""CLI entry point for ai_gitgen."""

from __future__ import annotations

import argparse
import sys

DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TEMPERATURE = 0.2
DEFAULT_MAX_TOKENS_COMMIT = 400
DEFAULT_MAX_TOKENS_PR = 700

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
        default=default_max_tokens,
        help=f"Maximum tokens in response (default: {default_max_tokens})",
    )
    subparser.add_argument(
        "--safe-mode",
        action="store_true",
        help="Mask obvious secrets in diff before sending to API",
    )


def _handle_commit(args: argparse.Namespace) -> int:
    print("not implemented yet", file=sys.stderr)
    return EXIT_USAGE


def _handle_pr(args: argparse.Namespace) -> int:
    print("not implemented yet", file=sys.stderr)
    return EXIT_USAGE


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
