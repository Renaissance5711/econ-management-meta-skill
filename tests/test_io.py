from pathlib import Path

from econ_management_meta.io import (
    canonical_json_bytes,
    read_json,
    read_yaml,
    sha256_data,
    sha256_file,
    write_json,
    write_yaml,
)


def test_canonical_hash_ignores_mapping_key_order() -> None:
    left = {"b": 2, "a": {"y": 1, "x": 0}}
    right = {"a": {"x": 0, "y": 1}, "b": 2}

    assert canonical_json_bytes(left) == canonical_json_bytes(right)
    assert sha256_data(left) == sha256_data(right)


def test_yaml_and_json_round_trip(tmp_path: Path) -> None:
    data = {"title": "AI与创新", "nested": {"enabled": True}}
    yaml_path = tmp_path / "data.yaml"
    json_path = tmp_path / "data.json"

    write_yaml(yaml_path, data)
    write_json(json_path, data)

    assert read_yaml(yaml_path) == data
    assert read_json(json_path) == data
    assert sha256_file(json_path)
