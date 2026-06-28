import csv
import json
import os
import tempfile

from tcia_cohort_forge.exporter import (
    export_collections_csv,
    export_manifest_csv,
    export_manifest_json,
    export_patients_csv,
    export_series_csv,
    export_studies_csv,
)
from tcia_cohort_forge.models import (
    CohortCriteria,
    CohortManifest,
    CollectionInfo,
    PatientInfo,
    SeriesInfo,
    StudyInfo,
)


def test_export_collections_csv():
    cols = [
        CollectionInfo(collection="TCGA-LUAD", count=500, authorized=True),
        CollectionInfo(collection="LIDC-IDRI", count=1018, authorized=False),
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name

    try:
        result = export_collections_csv(cols, path)
        assert result == path
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 3  # header + 2 data
        assert rows[0] == ["Collection", "PatientCount", "Authorized"]
        assert rows[1][0] == "TCGA-LUAD"
        assert rows[1][1] == "500"
    finally:
        os.unlink(path)


def test_export_patients_csv():
    pats = [
        PatientInfo(patient_id="P001", patient_sex="F", collection="TCGA-BRCA"),
        PatientInfo(patient_id="P002", patient_sex="M", collection="TCGA-BRCA"),
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name

    try:
        result = export_patients_csv(pats, path)
        assert result == path
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 3
        assert rows[1][0] == "P001"
    finally:
        os.unlink(path)


def test_export_studies_csv():
    studies = [
        StudyInfo(
            study_instance_uid="1.2.3.4",
            study_date="2020-01-01",
            patient_id="P001",
            collection="TEST",
            series_count=3,
        )
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name

    try:
        export_studies_csv(studies, path)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[1][0] == "1.2.3.4"
        assert rows[1][5] == "3"
    finally:
        os.unlink(path)


def test_export_series_csv():
    series = [
        SeriesInfo(
            series_instance_uid="1.2.3.4.5",
            modality="CT",
            body_part_examined="CHEST",
            collection="TEST",
            patient_id="P001",
        )
    ]
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name

    try:
        export_series_csv(series, path)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2
        assert rows[1][0] == "1.2.3.4.5"
        assert rows[1][1] == "CT"
    finally:
        os.unlink(path)


def test_export_manifest_csv():
    manifest = CohortManifest(
        criteria=CohortCriteria(collection="TEST"),
        patients=[PatientInfo(patient_id="P001", patient_sex="F")],
        studies=[StudyInfo(study_instance_uid="S1")],
        series=[
            SeriesInfo(
                series_instance_uid="X1",
                modality="CT",
                collection="TEST",
                patient_id="P001",
            )
        ],
        total_patients=1,
        total_studies=1,
        total_series=1,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
        path = f.name

    try:
        export_manifest_csv(manifest, path)
        with open(path) as f:
            reader = csv.reader(f)
            rows = list(reader)
        assert len(rows) == 2
        header = rows[0]
        assert "SeriesInstanceUID" in header
        assert "Modality" in header
    finally:
        os.unlink(path)


def test_export_manifest_json():
    manifest = CohortManifest(
        criteria=CohortCriteria(collection="TEST"),
        series=[
            SeriesInfo(series_instance_uid="X1", modality="CT", patient_id="P1"),
            SeriesInfo(series_instance_uid="X2", modality="MR", patient_id="P1"),
        ],
        total_series=2,
    )
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        path = f.name

    try:
        export_manifest_json(manifest, path)
        with open(path) as f:
            data = json.load(f)
        assert data["total_series"] == 2
        assert len(data["series"]) == 2
        assert data["series"][0]["modality"] == "CT"
        assert data["criteria"]["collection"] == "TEST"
    finally:
        os.unlink(path)
