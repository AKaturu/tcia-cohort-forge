from unittest.mock import MagicMock

import pytest

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.cohort import CohortBuilder
from tcia_cohort_forge.models import CohortCriteria, PatientInfo, SeriesInfo, StudyInfo


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock(spec=NbiaClient)


@pytest.fixture
def builder(mock_client: MagicMock) -> CohortBuilder:
    return CohortBuilder(client=mock_client)


def test_build_with_collection_only(builder: CohortBuilder, mock_client: MagicMock):
    mock_client.get_patients.return_value = [
        PatientInfo(patient_id="P1"),
        PatientInfo(patient_id="P2"),
    ]
    mock_client.get_studies.side_effect = [
        [StudyInfo(study_instance_uid="S1", patient_id="P1")],
        [StudyInfo(study_instance_uid="S2", patient_id="P2")],
    ]
    mock_client.get_series.side_effect = [
        [SeriesInfo(series_instance_uid="X1", modality="CT")],
        [SeriesInfo(series_instance_uid="X2", modality="CT")],
    ]

    criteria = CohortCriteria(collection="TCGA-LUAD")
    manifest = builder.build(criteria)

    assert manifest.total_patients == 2
    assert manifest.total_studies == 2
    assert manifest.total_series == 2


def test_build_with_modality_filter(builder: CohortBuilder, mock_client: MagicMock):
    mock_client.get_patients_by_modality.return_value = [PatientInfo(patient_id="P1")]
    mock_client.get_studies.return_value = [
        StudyInfo(study_instance_uid="S1", patient_id="P1"),
    ]
    mock_client.get_series.return_value = [
        SeriesInfo(series_instance_uid="X1", modality="CT"),
        SeriesInfo(series_instance_uid="X2", modality="MR"),
    ]

    criteria = CohortCriteria(collection="TEST", modalities=["CT"])
    manifest = builder.build(criteria)

    assert manifest.total_series == 1
    assert manifest.series[0].modality == "CT"


def test_build_with_body_part_filter(builder: CohortBuilder, mock_client: MagicMock):
    mock_client.get_patients.return_value = [PatientInfo(patient_id="P1")]
    mock_client.get_studies.return_value = [
        StudyInfo(study_instance_uid="S1", patient_id="P1"),
    ]
    mock_client.get_series.return_value = [
        SeriesInfo(series_instance_uid="X1", modality="CT", body_part_examined="CHEST"),
        SeriesInfo(series_instance_uid="X2", modality="CT", body_part_examined="ABDOMEN"),
    ]

    criteria = CohortCriteria(collection="TEST", body_parts=["CHEST"])
    manifest = builder.build(criteria)

    assert manifest.total_series == 1
    assert manifest.series[0].body_part_examined == "CHEST"


def test_build_multiple_patients_single_study_each(
    builder: CohortBuilder, mock_client: MagicMock
):
    mock_client.get_patients.return_value = [
        PatientInfo(patient_id="P1"),
        PatientInfo(patient_id="P2"),
    ]
    mock_client.get_studies.side_effect = [
        [StudyInfo(study_instance_uid="S1", patient_id="P1")],
        [StudyInfo(study_instance_uid="S2", patient_id="P2")],
    ]
    mock_client.get_series.side_effect = [
        [SeriesInfo(series_instance_uid="X1", modality="CT", patient_id="P1")],
        [SeriesInfo(series_instance_uid="X2", modality="MR", patient_id="P2")],
    ]

    criteria = CohortCriteria(collection="TEST")
    manifest = builder.build(criteria)

    assert manifest.total_patients == 2
    assert manifest.total_studies == 2
    assert manifest.total_series == 2


def test_build_no_collection(builder: CohortBuilder):
    criteria = CohortCriteria()
    manifest = builder.build(criteria)
    assert manifest.total_patients == 0


def test_build_with_patient_ids(builder: CohortBuilder, mock_client: MagicMock):
    mock_client.get_patients.return_value = [PatientInfo(patient_id="P1")]
    mock_client.get_studies.return_value = []
    mock_client.get_series.return_value = []

    criteria = CohortCriteria(collection="TEST", patient_ids=["P1"])
    manifest = builder.build(criteria)

    mock_client.get_patients.assert_called_with("TEST", patient_id="P1")
    assert manifest.total_patients == 1


def test_get_collection_summary(builder: CohortBuilder, mock_client: MagicMock):
    mock_client.get_patients.return_value = [PatientInfo(patient_id="P1")]
    mock_client.get_studies.return_value = [StudyInfo(study_instance_uid="S1")]
    mock_client.get_series.return_value = [SeriesInfo(series_instance_uid="X1")]
    mock_client.get_modality_counts.return_value = []
    mock_client.get_body_part_counts.return_value = []

    summary = builder.get_collection_summary("TEST")
    assert summary["collection"] == "TEST"
    assert summary["patients"] == 1
    assert summary["studies"] == 1
    assert summary["series"] == 1
