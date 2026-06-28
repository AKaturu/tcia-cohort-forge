from __future__ import annotations

import csv
import json
import os

from tcia_cohort_forge.models import (
    CohortManifest,
    CollectionInfo,
    PatientInfo,
    SeriesInfo,
    StudyInfo,
)


def export_series_csv(series: list[SeriesInfo], path: str) -> str:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "SeriesInstanceUID",
                "Modality",
                "BodyPartExamined",
                "SeriesDescription",
                "Collection",
                "PatientID",
                "Manufacturer",
                "SliceThickness",
            ]
        )
        for s in series:
            writer.writerow(
                [
                    s.series_instance_uid,
                    s.modality,
                    s.body_part_examined,
                    s.series_description,
                    s.collection,
                    s.patient_id,
                    s.manufacturer,
                    s.slice_thickness,
                ]
            )
    return path


def export_manifest_csv(manifest: CohortManifest, path: str) -> str:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "Collection",
                "PatientID",
                "PatientSex",
                "StudyInstanceUID",
                "StudyDate",
                "SeriesInstanceUID",
                "Modality",
                "BodyPartExamined",
                "SeriesDescription",
                "Manufacturer",
                "SliceThickness",
            ]
        )
        for s in manifest.series:
            writer.writerow(
                [
                    s.collection,
                    s.patient_id,
                    _find_patient_sex(manifest, s.patient_id),
                    s.study_instance_uid,
                    s.series_date,
                    s.series_instance_uid,
                    s.modality,
                    s.body_part_examined,
                    s.series_description,
                    s.manufacturer,
                    s.slice_thickness,
                ]
            )
    return path


def export_manifest_json(manifest: CohortManifest, path: str) -> str:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    data = {
        "criteria": manifest.criteria.model_dump(),
        "collections": manifest.collections,
        "total_patients": manifest.total_patients,
        "total_studies": manifest.total_studies,
        "total_series": manifest.total_series,
        "series": [s.model_dump() for s in manifest.series],
    }
    with open(path, "w") as f:
        json.dump(data, f, indent=2)
    return path


def export_collections_csv(collections: list[CollectionInfo], path: str) -> str:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Collection", "PatientCount", "Authorized"])
        for c in collections:
            writer.writerow([c.collection, c.count, c.authorized])
    return path


def export_patients_csv(patients: list[PatientInfo], path: str) -> str:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["PatientID", "PatientSex", "Collection", "Phantom"])
        for p in patients:
            writer.writerow([p.patient_id, p.patient_sex, p.collection, p.phantom])
    return path


def export_studies_csv(studies: list[StudyInfo], path: str) -> str:
    dir_path = os.path.dirname(path)
    if dir_path:
        os.makedirs(dir_path, exist_ok=True)

    with open(path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            [
                "StudyInstanceUID",
                "StudyDate",
                "StudyDescription",
                "PatientID",
                "Collection",
                "SeriesCount",
            ]
        )
        for s in studies:
            writer.writerow(
                [
                    s.study_instance_uid,
                    s.study_date,
                    s.study_description,
                    s.patient_id,
                    s.collection,
                    s.series_count,
                ]
            )
    return path


def _find_patient_sex(manifest: CohortManifest, patient_id: str) -> str:
    for p in manifest.patients:
        if p.patient_id == patient_id:
            return p.patient_sex
    return ""
