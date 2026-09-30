"""Command-line flow for AI-generated Git drafts."""

import argparse
from collections.abc import Sequence
import sys

from . import ai_client, prompts, security, validators
from .git_changes import GitError, collect


def _temperature(value: str) -> float:
    number = float(value)
    if not 0.0 <= number <= 2.0:
        raise argparse.ArgumentTypeError("temperature는 0.0~2.0이어야 합니다")
    return number


def _positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 정수여야 합니다")
    return number


def _positive_float(value: str) -> float:
    number = float(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("0보다 큰 수여야 합니다")
    return number


def _add_options(parser: argparse.ArgumentParser, max_tokens: int) -> None:
    parser.add_argument("--model", default="gpt-5.4-mini")
    parser.add_argument("--temperature", type=_temperature, default=0.2)
    parser.add_argument("--max-tokens", type=_positive_int, default=max_tokens)
    parser.add_argument("--timeout", type=_positive_float, default=30.0)
    parser.add_argument(
        "--safe-mode",
        action="store_true",
        help="diff의 민감정보를 마스킹한 후 API에 전송",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="ai-git",
        description="Git 변경사항으로 AI 커밋 메시지와 PR 초안을 생성합니다.",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    _add_options(commands.add_parser("commit", help="커밋 메시지 초안 생성"), 400)
    _add_options(commands.add_parser("pr", help="PR 제목과 본문 초안 생성"), 700)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return 0 for success or 1 for an execution error."""

    args = build_parser().parse_args(argv)
    try:
        snapshot = collect()
    except GitError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    if snapshot.empty:
        print("변경사항이 없습니다.")
        return 0

    if args.safe_mode:
        snapshot, masked_count = security.mask_snapshot(snapshot)
        print(
            f"안전 모드: 민감정보 {masked_count}건을 마스킹했습니다.",
            file=sys.stderr,
        )

    messages = prompts.build_messages(args.command, snapshot)
    temperature = args.temperature

    try:
        for attempt in range(2):
            generated = ai_client.complete(
                messages,
                model=args.model,
                temperature=temperature,
                max_tokens=args.max_tokens,
                timeout=args.timeout,
            )
            errors = validators.validate(args.command, generated)
            if not errors:
                break
            if attempt == 0:
                messages.append(
                    {
                        "role": "user",
                        "content": "다음 형식 오류를 고쳐 다시 작성하세요: "
                        + "; ".join(errors),
                    }
                )
                temperature /= 2
        else:
            print(
                "오류: AI 출력 형식을 두 번 검증했지만 실패했습니다: "
                + "; ".join(errors),
                file=sys.stderr,
            )
            return 1
    except ai_client.APIError as exc:
        print(f"오류: {exc}", file=sys.stderr)
        return 1

    print("=== 변경 요약 ===")
    print(f"변경 파일 {len(snapshot.files)}개")
    for path in snapshot.files:
        print(f"- {path}")
    label = "커밋 메시지" if args.command == "commit" else "PR"
    print(f"\n=== AI {label} 초안 ===")
    print(generated.strip())
    print("=== 초안 끝 ===")
    print("사용 전 실제 변경사항과 표현을 직접 검토·수정하세요.")
    return 0
