from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TypedDict, TypeVar

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.models import (
    CohortCriteria,
    CohortManifest,
    PatientInfo,
    SeriesInfo,
    StudyInfo,
)


class CollectionSummary(TypedDict):
    collection: str
    patients: int
    studies: int
    series: int
    modalities: int
    body_parts: int
    modality_list: list[str]
    body_part_list: list[str]


class CohortBuilder:
    def __init__(self, client: NbiaClient | None = None) -> None:
        self._owns_client = client is None
        self.client = client or NbiaClient()

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> CohortBuilder:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

    def build(self, criteria: CohortCriteria) -> CohortManifest:
        manifest = CohortManifest(criteria=criteria)

        if not criteria.collection:
            return manifest

        patients = _unique_by(self._resolve_patients(criteria), lambda patient: patient.patient_id)
        manifest.patients = patients
        manifest.total_patients = len(patients)

        patient_ids = [p.patient_id for p in patients]

        studies: list[StudyInfo] = []
        for pid in patient_ids:
            studies.extend(self.client.get_studies(criteria.collection, patient_id=pid))
        studies = _unique_by(studies, lambda study: study.study_instance_uid)
        manifest.studies = studies
        manifest.total_studies = len(studies)

        series: list[SeriesInfo] = []
        for s in studies:
            series.extend(
                self.client.get_series(
                    criteria.collection,
                    patient_id=s.patient_id,
                    study_uid=s.study_instance_uid,
                )
            )

        if criteria.modalities:
            mods_lower = {m.lower() for m in criteria.modalities}
            series = [s for s in series if s.modality.lower() in mods_lower]

        if criteria.body_parts:
            bp_lower = {b.lower() for b in criteria.body_parts}
            series = [s for s in series if s.body_part_examined.lower() in bp_lower]

        series = _unique_by(series, lambda item: item.series_instance_uid)
        manifest.series = series
        manifest.total_series = len(series)
        manifest.collections = [criteria.collection]

        return manifest

    def _resolve_patients(self, criteria: CohortCriteria) -> list[PatientInfo]:
        collection = criteria.collection
        if not collection:
            return []

        if criteria.patient_ids:
            matched_patients: list[PatientInfo] = []
            for pid in criteria.patient_ids:
                matched_patients.extend(self.client.get_patients(collection, patient_id=pid))
            return matched_patients

        if criteria.modalities:
            modality_patients: list[PatientInfo] = []
            for mod in criteria.modalities:
                modality_patients.extend(self.client.get_patients_by_modality(collection, mod))
            return modality_patients

        return self.client.get_patients(collection)

    def get_collection_summary(self, collection: str) -> CollectionSummary:
        patients = self.client.get_patients(collection)
        studies = self.client.get_studies(collection)
        series = self.client.get_series(collection)
        modalities = self.client.get_modality_counts(collection=collection)
        body_parts = self.client.get_body_part_counts(collection=collection)

        return {
            "collection": collection,
            "patients": len(patients),
            "studies": len(studies),
            "series": len(series),
            "modalities": len(modalities),
            "body_parts": len(body_parts),
            "modality_list": [m.modality for m in modalities],
            "body_part_list": [b.body_part for b in body_parts],
        }


_T = TypeVar("_T")


def _unique_by(items: Iterable[_T], key: Callable[[_T], str]) -> list[_T]:
    """Deduplicate stable nonempty identifiers while retaining source order."""
    seen: set[str] = set()
    unique: list[_T] = []
    for item in items:
        identity = key(item)
        if not identity or identity not in seen:
            unique.append(item)
        if identity:
            seen.add(identity)
    return unique
