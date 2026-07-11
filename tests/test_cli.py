from __future__ import annotations

import json
import zipfile
from io import BytesIO
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from typer.testing import CliRunner

import tcia_cohort_forge.cli as cli
from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.models import (
    BodyPartCount,
    CollectionInfo,
    ModalityCount,
    PatientInfo,
    SeriesInfo,
    SeriesSize,
    StudyInfo,
)

runner = CliRunner()


@pytest.fixture
def client(monkeypatch) -> MagicMock:
    managed = MagicMock(spec=NbiaClient)
    managed.__enter__.return_value = managed
    managed.__exit__.side_effect = lambda *_args: managed.close()
    monkeypatch.setattr(cli, "_get_client", lambda: managed)
    return managed


def _assert_closed(client: MagicMock) -> None:
    client.close.assert_called_once_with()


def test_collections_command_exports_csv(client: MagicMock, tmp_path: Path) -> None:
    client.get_collections.return_value = [
        CollectionInfo(collection="TEST", count=2, authorized=True)
    ]
    output = tmp_path / "collections.csv"

    result = runner.invoke(cli.app, ["collections", "--output", str(output)])

    assert result.exit_code == 0, result.output
    assert output.is_file()
    _assert_closed(client)


def test_patients_command_uses_modality_filter(client: MagicMock, tmp_path: Path) -> None:
    client.get_patients_by_modality.return_value = [
        PatientInfo(patient_id="P1", patient_sex="F", collection="TEST")
    ]
    output = tmp_path / "patients.csv"

    result = runner.invoke(
        cli.app,
        ["patients", "TEST", "--modality", "CT", "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    client.get_patients_by_modality.assert_called_once_with("TEST", "CT")
    assert output.is_file()
    _assert_closed(client)


def test_studies_command_exports_csv(client: MagicMock, tmp_path: Path) -> None:
    client.get_studies.return_value = [
        StudyInfo(
            study_instance_uid="STUDY-1",
            study_date="2020-01-01",
            patient_id="P1",
            collection="TEST",
        )
    ]
    output = tmp_path / "studies.csv"

    result = runner.invoke(
        cli.app,
        ["studies", "TEST", "--patient", "P1", "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert output.is_file()
    _assert_closed(client)


def test_series_command_filters_and_exports(client: MagicMock, tmp_path: Path) -> None:
    client.get_series.return_value = [
        SeriesInfo(series_instance_uid="CT-1", modality="CT", patient_id="P1"),
        SeriesInfo(series_instance_uid="MR-1", modality="MR", patient_id="P1"),
    ]
    output = tmp_path / "series.csv"

    result = runner.invoke(
        cli.app,
        ["series", "TEST", "--modality", "CT", "--output", str(output)],
    )

    assert result.exit_code == 0, result.output
    assert "CT-1" in output.read_text(encoding="utf-8")
    assert "MR-1" not in output.read_text(encoding="utf-8")
    _assert_closed(client)


def test_search_command_exports_manifest(client: MagicMock, tmp_path: Path) -> None:
    client.get_patients_by_modality.return_value = [
        PatientInfo(patient_id="P1", patient_sex="F", collection="TEST")
    ]
    client.get_studies.return_value = [
        StudyInfo(
            study_instance_uid="STUDY-1",
            study_date="2020-01-01",
            patient_id="P1",
            collection="TEST",
        )
    ]
    client.get_series.return_value = [
        SeriesInfo(
            series_instance_uid="SERIES-1",
            study_instance_uid="STUDY-1",
            modality="CT",
            patient_id="P1",
            collection="TEST",
        )
    ]
    output = tmp_path / "manifest.csv"
    json_output = tmp_path / "manifest.json"

    result = runner.invoke(
        cli.app,
        [
            "search",
            "TEST",
            "--modality",
            "CT",
            "--output",
            str(output),
            "--json",
            str(json_output),
        ],
    )

    assert result.exit_code == 0, result.output
    assert output.is_file() and json_output.is_file()
    assert json.loads(json_output.read_text(encoding="utf-8"))["total_series"] == 1
    _assert_closed(client)


def test_download_command_extracts_series(client: MagicMock, tmp_path: Path) -> None:
    archive = BytesIO()
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("image.dcm", b"dicom")
    client.get_series_size.return_value = SeriesSize(
        series_instance_uid="SERIES-1", series_size=5, image_count=1
    )
    client.download_series.return_value = archive.getvalue()

    result = runner.invoke(
        cli.app,
        ["download", "SERIES-1", "--output-dir", str(tmp_path / "downloads")],
    )

    assert result.exit_code == 0, result.output
    assert list((tmp_path / "downloads").rglob("image.dcm"))
    _assert_closed(client)


def test_download_cohort_dry_run(client: MagicMock, tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        json.dumps({"series": [{"series_instance_uid": "SERIES-1"}]}),
        encoding="utf-8",
    )

    result = runner.invoke(
        cli.app,
        ["download-cohort", str(manifest), "--dry-run"],
    )

    assert result.exit_code == 0, result.output
    assert "1 series would be downloaded" in result.output
    client.download_series.assert_not_called()
    _assert_closed(client)


def test_info_command_prints_collection_summary(client: MagicMock) -> None:
    client.get_patients.return_value = [PatientInfo(patient_id="P1")]
    client.get_studies.return_value = [StudyInfo(study_instance_uid="STUDY-1")]
    client.get_series.return_value = [SeriesInfo(series_instance_uid="SERIES-1")]
    client.get_modality_counts.return_value = [ModalityCount(modality="CT", count=1)]
    client.get_body_part_counts.return_value = [BodyPartCount(body_part="CHEST", count=1)]

    result = runner.invoke(cli.app, ["info", "TEST"])

    assert result.exit_code == 0, result.output
    assert "CHEST" in result.output
    _assert_closed(client)
