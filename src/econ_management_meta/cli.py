"""Command-line interface for the callable v0.1.0 core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import WorkflowError
from .locks import create_lock, verify_lock
from .profile import load_profile
from .project import initialize_project, validate_project
from .state import Stage, StageStatus, transition_stage


def _json_dump(payload: object, stream: Any = sys.stdout) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="emm")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("profile_dir", type=Path)
    validate_profile.add_argument("--schemas", type=Path, default=Path("schemas"))

    init = subparsers.add_parser("init")
    init.add_argument("topic")
    init.add_argument("--profile", type=Path, required=True)
    init.add_argument("--output", type=Path, required=True)
    init.add_argument("--schemas", type=Path, default=Path("schemas"))

    validate = subparsers.add_parser("validate-project")
    validate.add_argument("project_dir", type=Path)
    validate.add_argument("--schemas", type=Path, default=Path("schemas"))

    transition = subparsers.add_parser("transition")
    transition.add_argument("project_dir", type=Path)
    transition.add_argument("stage", choices=[stage.value for stage in Stage])
    transition.add_argument("status", choices=[status.value for status in StageStatus])
    transition.add_argument("--actor", required=True)
    transition.add_argument("--note", required=True)

    lock = subparsers.add_parser("lock")
    lock.add_argument("project_dir", type=Path)
    lock.add_argument("kind")
    lock.add_argument("version")
    lock.add_argument("artifacts", nargs="+", type=Path)
    lock.add_argument("--actor", required=True)

    verify = subparsers.add_parser("verify-lock")
    verify.add_argument("project_dir", type=Path)
    verify.add_argument("lock_path", type=Path)

    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, object]:
    if args.command == "version":
        return {"version": __version__}

    if args.command == "validate-profile":
        profile = load_profile(
            args.profile_dir,
            args.schemas / "profile.schema.json",
        )
        return {
            "valid": True,
            "profile": {
                "id": profile.id,
                "name": profile.name,
                "version": profile.version,
                "status": profile.status,
                "extends": profile.extends,
            },
        }

    if args.command == "init":
        project = initialize_project(
            args.topic,
            args.profile,
            args.output,
            args.schemas,
        )
        return {"created": True, "project": str(project.resolve())}

    if args.command == "validate-project":
        return validate_project(args.project_dir, args.schemas)

    if args.command == "transition":
        state = transition_stage(
            args.project_dir,
            Stage(args.stage),
            StageStatus(args.status),
            args.actor,
            args.note,
        )
        return {
            "updated": True,
            "stage": args.stage,
            "status": state["stages"][args.stage]["status"],
        }

    if args.command == "lock":
        lock_path = create_lock(
            args.project_dir,
            args.kind,
            args.version,
            args.artifacts,
            args.actor,
        )
        return {"created": True, "lock": str(lock_path.resolve())}

    if args.command == "verify-lock":
        return verify_lock(args.project_dir, args.lock_path)

    raise RuntimeError(f"Unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        payload = _dispatch(parser.parse_args(argv))
    except WorkflowError as error:
        _json_dump(error.as_dict(), sys.stderr)
        return 2
    except Exception as error:  # pragma: no cover - defensive CLI boundary
        _json_dump(
            {
                "error": "INTERNAL_ERROR",
                "message": str(error),
                "type": type(error).__name__,
            },
            sys.stderr,
        )
        return 1

    _json_dump(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
