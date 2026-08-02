"""Search provenance, bibliographic import, and report-level deduplication."""

from __future__ import annotations

import csv
import re
import shutil
import unicodedata
import xml.etree.ElementTree as ET
from collections import defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from .errors import ErrorCode, WorkflowError
from .io import read_json, read_yaml, sha256_file, write_yaml
from .tabular import append_unique_row, ensure_csv, read_csv_rows, require_human_actor, stable_id

_SEARCH_HEADERS = (
    "search_run_id", "created_at", "executed_by", "database", "platform",
    "search_date", "query", "hit_count", "export_batch", "registry_path",
)
_RECORD_HEADERS = (
    "record_id", "source_record_id", "search_run_id", "title", "authors", "year",
    "doi", "abstract", "journal", "source_file", "source_row", "provenance_id",
    "verification_status",
)
_DEDUP_HEADERS = (
    "record_id", "title", "authors", "year", "doi", "abstract", "journal",
    "source_record_ids", "search_run_ids", "provenance_ids", "source_record_count",
    "deduplication_status",
)
_CONFLICT_HEADERS = ("record_id", "field", "values", "source_record_ids", "recorded_by")


def _validate(data: Mapping[str, object], schema_path: Path, code: ErrorCode) -> None:
    validator = Draft202012Validator(read_json(schema_path), format_checker=FormatChecker())
    errors = sorted(validator.iter_errors(dict(data)), key=lambda item: list(item.absolute_path))
    if errors:
        raise WorkflowError(
            code,
            "search artifact does not satisfy its schema",
            {"errors": [{"path": ".".join(map(str, error.absolute_path)), "message": error.message} for error in errors]},
        )


def normalize_doi(value: str | None) -> str:
    text = (value or "").strip().casefold()
    text = re.sub(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)", "", text)
    return text.rstrip(" .;,)")


def normalize_title(value: str | None) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = text.replace("&", " and ").replace("—", " ").replace("–", " ")
    text = re.sub(r"[^\w]+", " ", text.casefold(), flags=re.UNICODE)
    return " ".join(text.split())


def register_search_run(
    project_dir: Path,
    run: Mapping[str, object],
    actor: str,
    schema_dir: Path,
) -> str:
    executed_by = require_human_actor(actor)
    search_run_id = stable_id(
        "SRCH", run.get("database"), run.get("platform"), run.get("search_date"),
        run.get("query"), run.get("export_batch"),
    )
    payload: dict[str, object] = {
        "search_run_id": search_run_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "executed_by": executed_by,
        **dict(run),
    }
    _validate(payload, schema_dir / "search-run.schema.json", ErrorCode.SEARCH_IMPORT_INVALID)
    registry_dir = project_dir / "02_search" / "search-runs"
    path = registry_dir / f"{search_run_id}.yaml"
    if path.exists():
        raise WorkflowError(
            ErrorCode.ARTIFACT_ALREADY_EXISTS,
            "this search run has already been registered",
            {"path": str(path)},
        )
    write_yaml(path, payload)
    append_unique_row(
        project_dir / "02_search/evidence-source-registry.csv",
        _SEARCH_HEADERS,
        {**payload, "registry_path": path.relative_to(project_dir).as_posix()},
        ("search_run_id",),
    )
    return search_run_id


def _field(row: Mapping[str, object], *names: str) -> str:
    lookup = {str(key).casefold().strip(): value for key, value in row.items()}
    for name in names:
        value = lookup.get(name.casefold())
        if value is not None:
            return str(value).strip()
    return ""


def _parse_csv(path: Path) -> list[dict[str, str]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return [
        {
            "source_record_id": _field(row, "id", "record_id", "ut", "accession_number") or str(index),
            "title": _field(row, "title", "article title", "ti"),
            "authors": _field(row, "authors", "author", "au"),
            "year": _field(row, "year", "publication year", "py")[:4],
            "doi": normalize_doi(_field(row, "doi", "digital object identifier")),
            "abstract": _field(row, "abstract", "ab"),
            "journal": _field(row, "journal", "source title", "jo"),
            "source_row": str(index),
        }
        for index, row in enumerate(rows, start=2)
    ]


def _parse_ris(path: Path) -> list[dict[str, str]]:
    entries: list[dict[str, list[str]]] = []
    current: dict[str, list[str]] = defaultdict(list)
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        match = re.match(r"^([A-Z0-9]{2})  - ?(.*)$", line)
        if not match:
            continue
        tag, value = match.groups()
        if tag == "ER":
            if current:
                entries.append(dict(current))
                current = defaultdict(list)
        else:
            current[tag].append(value.strip())
    if current:
        entries.append(dict(current))

    parsed = []
    for index, entry in enumerate(entries, start=1):
        source_id = (entry.get("ID") or entry.get("AN") or [str(index)])[0]
        title = (entry.get("TI") or entry.get("T1") or [""])[0]
        year = (entry.get("PY") or entry.get("Y1") or [""])[0][:4]
        parsed.append({
            "source_record_id": source_id,
            "title": title,
            "authors": "; ".join(entry.get("AU") or entry.get("A1") or []),
            "year": year,
            "doi": normalize_doi((entry.get("DO") or [""])[0]),
            "abstract": (entry.get("AB") or [""])[0],
            "journal": (entry.get("JO") or entry.get("T2") or [""])[0],
            "source_row": str(index),
        })
    return parsed


def _parse_bibtex(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8-sig")
    starts = list(re.finditer(r"@\w+\s*\{\s*([^,]+),", text, flags=re.IGNORECASE))
    entries: list[dict[str, str]] = []
    for index, start in enumerate(starts):
        end = starts[index + 1].start() if index + 1 < len(starts) else len(text)
        block = text[start.end():end]
        fields = {
            key.casefold(): value.strip()
            for key, value in re.findall(
                r"(?ms)^\s*([A-Za-z][\w-]*)\s*=\s*[\{\"](.*?)[\}\"]\s*,?\s*$",
                block,
            )
        }
        entries.append({
            "source_record_id": start.group(1).strip(),
            "title": fields.get("title", "").replace("{", "").replace("}", ""),
            "authors": fields.get("author", "").replace(" and ", "; "),
            "year": fields.get("year", "")[:4],
            "doi": normalize_doi(fields.get("doi", "")),
            "abstract": fields.get("abstract", ""),
            "journal": fields.get("journal", ""),
            "source_row": str(index + 1),
        })
    return entries


def _element_text(element: ET.Element | None) -> str:
    return "" if element is None else "".join(element.itertext()).strip()


def _parse_endnote_xml(path: Path) -> list[dict[str, str]]:
    root = ET.parse(path).getroot()
    parsed = []
    for index, record in enumerate(root.findall(".//record"), start=1):
        authors = [_element_text(element) for element in record.findall(".//contributors/authors/author")]
        parsed.append({
            "source_record_id": _element_text(record.find("./rec-number")) or str(index),
            "title": _element_text(record.find(".//titles/title")),
            "authors": "; ".join(value for value in authors if value),
            "year": _element_text(record.find(".//dates/year"))[:4],
            "doi": normalize_doi(_element_text(record.find(".//electronic-resource-num"))),
            "abstract": _element_text(record.find(".//abstract")),
            "journal": _element_text(record.find(".//titles/secondary-title")),
            "source_row": str(index),
        })
    return parsed


def _parse(path: Path, source_format: str) -> list[dict[str, str]]:
    parsers = {
        "csv": _parse_csv,
        "ris": _parse_ris,
        "bibtex": _parse_bibtex,
        "endnote-xml": _parse_endnote_xml,
    }
    parser = parsers.get(source_format.casefold())
    if parser is None:
        raise WorkflowError(
            ErrorCode.SEARCH_IMPORT_INVALID,
            "unsupported bibliographic source format",
            {"format": source_format, "supported": sorted(parsers)},
        )
    try:
        rows = parser(path)
    except (OSError, csv.Error, ET.ParseError, UnicodeError) as exc:
        raise WorkflowError(
            ErrorCode.SEARCH_IMPORT_INVALID,
            "bibliographic source could not be parsed",
            {"path": str(path), "format": source_format, "reason": str(exc)},
        ) from exc
    if not rows:
        raise WorkflowError(
            ErrorCode.SEARCH_IMPORT_INVALID,
            "bibliographic source contains no parseable records",
            {"path": str(path), "format": source_format},
        )
    return rows


def import_search_file(
    project_dir: Path,
    search_run_id: str,
    source_path: Path,
    source_format: str,
    actor: str,
    schema_dir: Path,
) -> dict[str, int]:
    require_human_actor(actor)
    run_path = project_dir / "02_search/search-runs" / f"{search_run_id}.yaml"
    if not run_path.is_file():
        raise WorkflowError(
            ErrorCode.SEARCH_IMPORT_INVALID,
            "search run must be registered before records are imported",
            {"search_run_id": search_run_id},
        )
    if not source_path.is_file():
        raise WorkflowError(
            ErrorCode.SEARCH_IMPORT_INVALID,
            "bibliographic source file does not exist",
            {"path": str(source_path)},
        )

    parsed = _parse(source_path, source_format)
    destination = project_dir / "02_search/raw-exports" / f"{search_run_id}-{source_path.name}"
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists() and sha256_file(destination) != sha256_file(source_path):
        raise WorkflowError(
            ErrorCode.ARTIFACT_ALREADY_EXISTS,
            "a different raw export already occupies this provenance path",
            {"path": str(destination)},
        )
    if not destination.exists():
        shutil.copy2(source_path, destination)

    imported_path = project_dir / "02_search/imported-records.csv"
    imported = 0
    for row in parsed:
        title = row["title"].strip()
        if not title:
            raise WorkflowError(
                ErrorCode.SEARCH_IMPORT_INVALID,
                "an imported record is missing its title",
                {"source_file": source_path.name, "source_row": row["source_row"]},
            )
        source_record_id = row["source_record_id"]
        payload = {
            "record_id": stable_id("REC", search_run_id, source_record_id),
            "source_record_id": source_record_id,
            "search_run_id": search_run_id,
            "title": title,
            "authors": row["authors"],
            "year": row["year"],
            "doi": normalize_doi(row["doi"]),
            "abstract": row["abstract"],
            "journal": row["journal"],
            "source_file": destination.relative_to(project_dir).as_posix(),
            "source_row": row["source_row"],
            "provenance_id": stable_id("PROV", search_run_id, source_record_id, sha256_file(destination)),
            "verification_status": "IMPORTED",
        }
        _validate(payload, schema_dir / "bibliographic-record.schema.json", ErrorCode.SEARCH_IMPORT_INVALID)
        append_unique_row(imported_path, _RECORD_HEADERS, payload, ("record_id",))
        imported += 1
    return {"imported": imported}


def _write_rows(path: Path, headers: tuple[str, ...], rows: Iterable[Mapping[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(headers))
        writer.writeheader()
        for row in rows:
            writer.writerow({header: row.get(header, "") for header in headers})
    temporary.replace(path)


def deduplicate_records(project_dir: Path, actor: str) -> dict[str, int]:
    recorded_by = require_human_actor(actor)
    source_rows = read_csv_rows(project_dir / "02_search/imported-records.csv")
    if not source_rows:
        raise WorkflowError(
            ErrorCode.SEARCH_IMPORT_INVALID,
            "no imported records are available for deduplication",
            {"path": "02_search/imported-records.csv"},
        )

    groups: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in source_rows:
        doi = normalize_doi(row["doi"])
        title = normalize_title(row["title"])
        key = f"doi:{doi}" if doi else f"title-year:{title}:{row['year']}"
        groups[key].append(row)

    deduplicated: list[dict[str, object]] = []
    conflicts: list[dict[str, object]] = []
    for key in sorted(groups):
        group = sorted(groups[key], key=lambda item: item["record_id"])
        record_id = stable_id("REC", "deduplicated", key)
        for field in ("title", "year", "doi"):
            values = sorted({row[field].strip() for row in group if row[field].strip()})
            if len(values) > 1:
                conflicts.append({
                    "record_id": record_id,
                    "field": field,
                    "values": "|".join(values),
                    "source_record_ids": "|".join(row["source_record_id"] for row in group),
                    "recorded_by": recorded_by,
                })
        def first(field: str) -> str:
            return next((row[field] for row in group if row[field].strip()), "")
        deduplicated.append({
            "record_id": record_id,
            "title": first("title"),
            "authors": first("authors"),
            "year": first("year"),
            "doi": first("doi"),
            "abstract": first("abstract"),
            "journal": first("journal"),
            "source_record_ids": "|".join(row["source_record_id"] for row in group),
            "search_run_ids": "|".join(sorted({row["search_run_id"] for row in group})),
            "provenance_ids": "|".join(row["provenance_id"] for row in group),
            "source_record_count": len(group),
            "deduplication_status": "HUMAN_REVIEW_REQUIRED" if len(group) > 1 else "UNIQUE",
        })

    _write_rows(project_dir / "02_search/deduplicated-records.csv", _DEDUP_HEADERS, deduplicated)
    _write_rows(project_dir / "02_search/deduplication-conflicts.csv", _CONFLICT_HEADERS, conflicts)
    return {
        "source_records": len(source_rows),
        "deduplicated_records": len(deduplicated),
        "duplicates_merged": len(source_rows) - len(deduplicated),
        "conflicts": len(conflicts),
    }
