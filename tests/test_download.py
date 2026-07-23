from pathlib import Path

from learning_analytics.download import EXPECTED_SHA256, sha256


def test_sha256(tmp_path: Path) -> None:
    source = tmp_path / "value.txt"
    source.write_text("OULAD\n", encoding="utf-8")
    assert sha256(source) == "66124ecf336d23c25aa825a5a8e6c21d04348b91497271069a7553fc76778f01"
    assert len(EXPECTED_SHA256) == 64
