"""Command-line interface for the callable workflow core."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from . import __version__
from .errors import WorkflowError
from .extraction import (
    export_verified_extraction,
    list_extraction_conflicts,
    record_extraction,
    resolve_extraction,
)
from .io import read_yaml
from .locks import create_lock, verify_lock
from .profile import load_profile
from .project import initialize_project, validate_project
from .protocol import create_amendment, create_protocol, validate_protocol
from .reports import assign_report_family, export_report_family_map
from .screening import (
    export_screening_consensus,
    record_screening_decision,
    resolve_screening_conflict,
    screening_agreement,
)
from .search import deduplicate_records, import_search_file, register_search_run
from .state import Stage, StageStatus, transition_stage


def _json_dump(payload: object, stream: Any = sys.stdout) -> None:
    stream.write(json.dumps(payload, ensure_ascii=False, sort_keys=True) + "\n")


def _add_schemas(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--schemas", type=Path, default=Path("schemas"))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="emm")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("version")

    validate_profile = subparsers.add_parser("validate-profile")
    validate_profile.add_argument("profile_dir", type=Path)
    _add_schemas(validate_profile)

    init = subparsers.add_parser("init")
    init.add_argument("topic")
    init.add_argument("--profile", type=Path, required=True)
    init.add_argument("--output", type=Path, required=True)
    _add_schemas(init)

    validate = subparsers.add_parser("validate-project")
    validate.add_argument("project_dir", type=Path)
    _add_schemas(validate)

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

    protocol = subparsers.add_parser("protocol")
    protocol_sub = protocol.add_subparsers(dest="protocol_command", required=True)
    protocol_create = protocol_sub.add_parser("create")
    protocol_create.add_argument("project_dir", type=Path)
    protocol_create.add_argument("version")
    protocol_create.add_argument("source", type=Path)
    protocol_create.add_argument("--actor", required=True)
    _add_schemas(protocol_create)
    protocol_validate = protocol_sub.add_parser("validate")
    protocol_validate.add_argument("path", type=Path)
    _add_schemas(protocol_validate)
    protocol_amend = protocol_sub.add_parser("amend")
    protocol_amend.add_argument("project_dir", type=Path)
    protocol_amend.add_argument("source", type=Path)
    protocol_amend.add_argument("--actor", required=True)
    _add_schemas(protocol_amend)

    search = subparsers.add_parser("search")
    search_sub = search.add_subparsers(dest="search_command", required=True)
    search_register = search_sub.add_parser("register")
    search_register.add_argument("project_dir", type=Path)
    search_register.add_argument("source", type=Path)
    search_register.add_argument("--actor", required=True)
    _add_schemas(search_register)
    search_import = search_sub.add_parser("import")
    search_import.add_argument("project_dir", type=Path)
    search_import.add_argument("search_run_id")
    search_import.add_argument("source", type=Path)
    search_import.add_argument("--format", required=True)
    search_import.add_argument("--actor", required=True)
    _add_schemas(search_import)
    search_dedup = search_sub.add_parser("deduplicate")
    search_dedup.add_argument("project_dir", type=Path)
    search_dedup.add_argument("--actor", required=True)

    screen = subparsers.add_parser("screen")
    screen_sub = screen.add_subparsers(dest="screen_command", required=True)
    screen_decide = screen_sub.add_parser("decide")
    screen_decide.add_argument("project_dir", type=Path)
    screen_decide.add_argument("stage", choices=["title-abstract", "fulltext"])
    screen_decide.add_argument("record_id")
    screen_decide.add_argument("reviewer")
    screen_decide.add_argument("decision", choices=["INCLUDE", "EXCLUDE", "UNCERTAIN"])
    screen_decide.add_argument("--reason")
    screen_decide.add_argument("--page")
    screen_decide.add_argument("--note")
    _add_schemas(screen_decide)
    screen_agreement_parser = screen_sub.add_parser("agreement")
    screen_agreement_parser.add_argument("project_dir", type=Path)
    screen_agreement_parser.add_argument("stage", choices=["title-abstract", "fulltext"])
    screen_resolve = screen_sub.add_parser("resolve")
    screen_resolve.add_argument("project_dir", type=Path)
    screen_resolve.add_argument("stage", choices=["title-abstract", "fulltext"])
    screen_resolve.add_argument("record_id")
    screen_resolve.add_argument("adjudicator")
    screen_resolve.add_argument("final_decision", choices=["INCLUDE", "EXCLUDE"])
    screen_resolve.add_argument("--reason")
    screen_resolve.add_argument("--page")
    screen_resolve.add_argument("--rationale", required=True)
    _add_schemas(screen_resolve)
    screen_consensus = screen_sub.add_parser("consensus")
    screen_consensus.add_argument("project_dir", type=Path)
    screen_consensus.add_argument("stage", choices=["title-abstract", "fulltext"])

    report_family = subparsers.add_parser("report-family")
    report_sub = report_family.add_subparsers(dest="report_command", required=True)
    report_assign = report_sub.add_parser("assign")
    report_assign.add_argument("project_dir", type=Path)
    report_assign.add_argument("report_id")
    report_assign.add_argument("report_family_id")
    report_assign.add_argument("study_id")
    report_assign.add_argument("version_role")
    report_assign.add_argument("--actor", required=True)
    report_assign.add_argument("--evidence", required=True)
    _add_schemas(report_assign)
    report_export = report_sub.add_parser("export")
    report_export.add_argument("project_dir", type=Path)

    extract = subparsers.add_parser("extract")
    extract_sub = extract.add_subparsers(dest="extract_command", required=True)
    extract_record = extract_sub.add_parser("record")
    extract_record.add_argument("project_dir", type=Path)
    extract_record.add_argument("report_id")
    extract_record.add_argument("study_id")
    extract_record.add_argument("field_id")
    extract_record.add_argument("extractor")
    extract_record.add_argument("value_json")
    extract_record.add_argument("--page", required=True)
    extract_record.add_argument("--quote", required=True)
    _add_schemas(extract_record)
    extract_conflicts = extract_sub.add_parser("conflicts")
    extract_conflicts.add_argument("project_dir", type=Path)
    extract_resolve = extract_sub.add_parser("resolve")
    extract_resolve.add_argument("project_dir", type=Path)
    extract_resolve.add_argument("report_id")
    extract_resolve.add_argument("study_id")
    extract_resolve.add_argument("field_id")
    extract_resolve.add_argument("value_json")
    extract_resolve.add_argument("--resolver", required=True)
    extract_resolve.add_argument("--rationale", required=True)
    extract_export = extract_sub.add_parser("export")
    extract_export.add_argument("project_dir", type=Path)

    return parser


def _dispatch(args: argparse.Namespace) -> dict[str, object]:
    if args.command == "version":
        return {"version": __version__}
    if args.command == "validate-profile":
        profile = load_profile(args.profile_dir, args.schemas / "profile.schema.json")
        return {"valid": True, "profile": {"id": profile.id, "name": profile.name, "version": profile.version, "status": profile.status, "extends": profile.extends}}
    if args.command == "init":
        project = initialize_project(args.topic, args.profile, args.output, args.schemas)
        return {"created": True, "project": str(project.resolve())}
    if args.command == "validate-project":
        return validate_project(args.project_dir, args.schemas)
    if args.command == "transition":
        state = transition_stage(args.project_dir, Stage(args.stage), StageStatus(args.status), args.actor, args.note)
        return {"updated": True, "stage": args.stage, "status": state["stages"][args.stage]["status"]}
    if args.command == "lock":
        lock_path = create_lock(args.project_dir, args.kind, args.version, args.artifacts, args.actor)
        return {"created": True, "lock": str(lock_path.resolve())}
    if args.command == "verify-lock":
        return verify_lock(args.project_dir, args.lock_path)

    if args.command == "protocol":
        if args.protocol_command == "create":
            path = create_protocol(args.project_dir, args.version, read_yaml(args.source), args.actor, args.schemas)
            return {"created": True, "path": str(path.resolve()), "version": args.version}
        if args.protocol_command == "validate":
            return validate_protocol(args.path, args.schemas)
        if args.protocol_command == "amend":
            path = create_amendment(args.project_dir, read_yaml(args.source), args.actor, args.schemas)
            return {"created": True, "path": str(path.resolve())}

    if args.command == "search":
        if args.search_command == "register":
            search_run_id = register_search_run(args.project_dir, read_yaml(args.source), args.actor, args.schemas)
            return {"created": True, "search_run_id": search_run_id}
        if args.search_command == "import":
            return import_search_file(args.project_dir, args.search_run_id, args.source, args.format, args.actor, args.schemas)
        if args.search_command == "deduplicate":
            return deduplicate_records(args.project_dir, args.actor)

    if args.command == "screen":
        if args.screen_command == "decide":
            decision_id = record_screening_decision(args.project_dir, args.stage, args.record_id, args.reviewer, args.decision, args.reason or None, args.page or None, args.note or None, args.schemas)
            return {"created": True, "decision_id": decision_id}
        if args.screen_command == "agreement":
            return screening_agreement(args.project_dir, args.stage)
        if args.screen_command == "resolve":
            resolution_id = resolve_screening_conflict(args.project_dir, args.stage, args.record_id, args.adjudicator, args.final_decision, args.reason or None, args.page or None, args.rationale, args.schemas)
            return {"created": True, "resolution_id": resolution_id}
        if args.screen_command == "consensus":
            path = export_screening_consensus(args.project_dir, args.stage)
            return {"created": True, "path": str(path.resolve())}

    if args.command == "report-family":
        if args.report_command == "assign":
            assignment_id = assign_report_family(args.project_dir, args.report_id, args.report_family_id, args.study_id, args.version_role, args.actor, args.evidence, args.schemas)
            return {"created": True, "assignment_id": assignment_id}
        if args.report_command == "export":
            path = export_report_family_map(args.project_dir)
            return {"created": True, "path": str(path.resolve())}

    if args.command == "extract":
        if args.extract_command == "record":
            extraction_id = record_extraction(args.project_dir, args.report_id, args.study_id, args.field_id, args.extractor, json.loads(args.value_json), args.page, args.quote, args.schemas)
            return {"created": True, "extraction_id": extraction_id}
        if args.extract_command == "conflicts":
            return {"conflicts": list_extraction_conflicts(args.project_dir)}
        if args.extract_command == "resolve":
            resolution_id = resolve_extraction(args.project_dir, args.report_id, args.study_id, args.field_id, args.resolver, json.loads(args.value_json), args.rationale)
            return {"created": True, "resolution_id": resolution_id}
        if args.extract_command == "export":
            path = export_verified_extraction(args.project_dir)
            return {"created": True, "path": str(path.resolve())}

    raise RuntimeError(f"Unhandled command: {args.command}")


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    try:
        payload = _dispatch(parser.parse_args(argv))
    except WorkflowError as error:
        _json_dump(error.as_dict(), sys.stderr)
        return 2
    except Exception as error:  # pragma: no cover - defensive CLI boundary
        _json_dump({"error": "INTERNAL_ERROR", "message": str(error), "type": type(error).__name__}, sys.stderr)
        return 1
    _json_dump(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
