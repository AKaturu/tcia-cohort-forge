from tcia_cohort_forge.models import (
    BodyPartCount,
    CohortCriteria,
    CohortManifest,
    CollectionDetail,
    CollectionInfo,
    DicomTag,
    DownloadResult,
    ManufacturerCount,
    ModalityCount,
    PatientInfo,
    SeriesInfo,
    SeriesSize,
    StudyInfo,
)


def test_collection_info_defaults():
    c = CollectionInfo(collection="TCGA-LUAD")
    assert c.collection == "TCGA-LUAD"
    assert c.count == 0
    assert c.authorized is True


def test_collection_info_full():
    c = CollectionInfo(collection="LIDC-IDRI", count=1018, authorized=False)
    assert c.count == 1018
    assert c.authorized is False


def test_collection_detail():
    d = CollectionDetail(
        collection_name="4D-Lung",
        description="<p>4D Lung CT images</p>",
        description_uri="https://doi.org/10.7937/...",
        id=101,
    )
    assert d.collection_name == "4D-Lung"
    assert d.id == 101


def test_patient_info():
    p = PatientInfo(
        patient_id="P001",
        patient_sex="F",
        collection="TCGA-BRCA",
        phantom=False,
    )
    assert p.patient_id == "P001"
    assert p.patient_sex == "F"
    assert p.phantom is False


def test_study_info():
    s = StudyInfo(
        study_instance_uid="1.2.3.4.5.6",
        study_date="2020-01-15",
        patient_id="P001",
        collection="TCGA-BRCA",
        series_count=3,
    )
    assert s.study_instance_uid == "1.2.3.4.5.6"
    assert s.series_count == 3


def test_series_info():
    s = SeriesInfo(
        series_instance_uid="1.2.3.4.5.6.7",
        modality="CT",
        body_part_examined="CHEST",
        patient_id="P001",
        num_images=200,
        slice_thickness=1.25,
    )
    assert s.modality == "CT"
    assert s.num_images == 200
    assert s.slice_thickness == 1.25


def test_series_size():
    ss = SeriesSize(
        series_instance_uid="1.2.3.4",
        series_size=1048576,
        image_count=150,
    )
    assert ss.series_size == 1048576
    assert ss.image_count == 150


def test_dicom_tag():
    dt = DicomTag(element="(0028,0010)", name="Rows", data="512")
    assert dt.name == "Rows"
    assert dt.data == "512"


def test_body_part_count():
    bp = BodyPartCount(body_part="LUNG", count=500, authorized=True)
    assert bp.body_part == "LUNG"
    assert bp.count == 500


def test_modality_count():
    mc = ModalityCount(modality="CT", count=1000, authorized=True)
    assert mc.modality == "CT"
    assert mc.count == 1000


def test_manufacturer_count():
    mc = ManufacturerCount(manufacturer="GE Medical Systems", count=200)
    assert mc.manufacturer == "GE Medical Systems"
    assert mc.count == 200


def test_cohort_criteria_defaults():
    cc = CohortCriteria()
    assert cc.collection is None
    assert cc.modalities == []
    assert cc.body_parts == []


def test_cohort_criteria_full():
    cc = CohortCriteria(
        collection="TCGA-LUAD",
        modalities=["CT", "PT"],
        body_parts=["CHEST"],
        patient_sex="Male",
    )
    assert cc.collection == "TCGA-LUAD"
    assert len(cc.modalities) == 2


def test_cohort_manifest_defaults():
    cm = CohortManifest()
    assert cm.total_patients == 0
    assert cm.total_series == 0
    assert cm.series == []


def test_cohort_manifest_with_data():
    cm = CohortManifest(
        criteria=CohortCriteria(collection="TEST"),
        patients=[PatientInfo(patient_id="P1")],
        series=[SeriesInfo(series_instance_uid="S1")],
        total_patients=1,
        total_series=1,
    )
    assert cm.total_patients == 1
    assert len(cm.series) == 1


def test_download_result_defaults():
    dr = DownloadResult(output_dir="/tmp/downloads")
    assert dr.output_dir == "/tmp/downloads"
    assert dr.total_files == 0
    assert dr.errors == []
