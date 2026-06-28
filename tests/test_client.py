from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.config import Settings


@pytest.fixture
def client() -> NbiaClient:
    settings = Settings(api_base_url="https://fake-tcia.example.com/v4")
    c = NbiaClient(settings)
    c._get = MagicMock()
    return c


def test_get_collections(client: NbiaClient):
    client._get.return_value = [
        {"collection": "TCGA-LUAD", "count": 500, "Authorized": "1"},
        {"collection": "LIDC-IDRI", "count": 1018, "Authorized": "1"},
    ]
    cols = client.get_collections()
    assert len(cols) == 2
    assert cols[0].collection == "TCGA-LUAD"
    assert cols[0].count == 500
    assert cols[0].authorized is True


def test_get_collection_names(client: NbiaClient):
    client._get.return_value = [{"collection": "TCGA-LUAD"}, {"collection": "LIDC-IDRI"}]
    names = client.get_collection_names()
    assert names == ["TCGA-LUAD", "LIDC-IDRI"]


def test_get_patients(client: NbiaClient):
    client._get.return_value = [
        {"PatientId": "TCGA-01", "PatientSex": "F", "Collection": "TCGA-BRCA"},
        {"PatientId": "TCGA-02", "PatientSex": "M", "Collection": "TCGA-BRCA"},
    ]
    pats = client.get_patients("TCGA-BRCA")
    assert len(pats) == 2
    assert pats[0].patient_id == "TCGA-01"
    assert pats[0].patient_sex == "F"


def test_get_studies(client: NbiaClient):
    client._get.return_value = [
        {
            "StudyInstanceUID": "1.2.3.4",
            "StudyDate": "2020-01-01",
            "PatientId": "P001",
            "Collection": "TCGA-LUAD",
            "SeriesCount": "3",
        }
    ]
    studies = client.get_studies("TCGA-LUAD")
    assert len(studies) == 1
    assert studies[0].study_instance_uid == "1.2.3.4"
    assert studies[0].series_count == 3


def test_get_series(client: NbiaClient):
    client._get.return_value = [
        {
            "SeriesInstanceUID": "1.2.3.4.5",
            "Modality": "CT",
            "BodyPartExamined": "CHEST",
            "PatientId": "P001",
            "Collection": "TCGA-LUAD",
        }
    ]
    series = client.get_series("TCGA-LUAD")
    assert len(series) == 1
    assert series[0].modality == "CT"
    assert series[0].body_part_examined == "CHEST"


def test_get_series_size(client: NbiaClient):
    client._get.return_value = [
        {"SeriesInstanceUID": "1.2.3.4", "SeriesSize": "5000000", "ImageCount": "300"}
    ]
    ss = client.get_series_size("1.2.3.4")
    assert ss.series_size == 5000000
    assert ss.image_count == 300


def test_get_dicom_tags(client: NbiaClient):
    client._get.return_value = [
        {"element": "(0028,0010)", "name": "Rows", "data": "512"},
        {"element": "(0028,0011)", "name": "Columns", "data": "512"},
    ]
    tags = client.get_dicom_tags("1.2.3.4")
    assert len(tags) == 2
    assert tags[0].name == "Rows"


def test_get_body_part_counts(client: NbiaClient):
    client._get.return_value = [
        {"bodyPart": "LUNG", "count": "200", "Authorized": "1"},
        {"bodyPart": "BRAIN", "count": "150", "Authorized": "1"},
    ]
    bps = client.get_body_part_counts()
    assert len(bps) == 2
    assert bps[0].body_part == "LUNG"
    assert bps[0].count == 200


def test_get_modality_counts(client: NbiaClient):
    client._get.return_value = [
        {"modality": "CT", "count": "800", "Authorized": "1"},
        {"modality": "MR", "count": "400", "Authorized": "1"},
    ]
    mods = client.get_modality_counts(collection="TCGA-LUAD")
    assert len(mods) == 2
    assert mods[0].modality == "CT"


def test_get_manufacturer_counts(client: NbiaClient):
    client._get.return_value = [
        {"manufacturer": "GE", "count": "100", "Authorized": "1"},
    ]
    mfrs = client.get_manufacturer_counts()
    assert len(mfrs) == 1
    assert mfrs[0].manufacturer == "GE"


def test_download_series(client: NbiaClient):
    client._client.get = MagicMock()
    client._client.get.return_value = MagicMock()
    client._client.get.return_value.content = b"fake-zip-content"
    client._client.get.return_value.raise_for_status = MagicMock()

    data = client.download_series("1.2.3.4")
    assert data == b"fake-zip-content"


def test_get_patients_by_modality(client: NbiaClient):
    client._get.return_value = [
        {"PatientId": "P001"},
        {"PatientId": "P002"},
    ]
    pats = client.get_patients_by_modality("TEST", "CT")
    assert len(pats) == 2
    assert pats[0].patient_id == "P001"
