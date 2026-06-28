from __future__ import annotations

from typing import Any

import httpx

from tcia_cohort_forge.config import Settings
from tcia_cohort_forge.models import (
    BodyPartCount,
    CollectionDetail,
    CollectionInfo,
    DicomTag,
    ManufacturerCount,
    ModalityCount,
    PatientInfo,
    SeriesInfo,
    SeriesSize,
    StudyInfo,
)


class NbiaClient:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings()
        self._client = httpx.Client(
            timeout=self.settings.request_timeout,
            headers={"User-Agent": self.settings.user_agent},
        )
        if self.settings.auth_token:
            self._client.headers["Authorization"] = f"Bearer {self.settings.auth_token}"

    def _get(self, endpoint: str, params: dict[str, Any] | None = None) -> Any:
        url = self.settings.get_api_url(endpoint)
        p = params or {}
        p.setdefault("format", "json")
        resp = self._client.get(url, params=p)
        resp.raise_for_status()
        if not resp.text.strip():
            return []
        return resp.json()

    def _post_form(
        self, endpoint: str, data: dict[str, Any] | None = None
    ) -> Any:
        url = self.settings.get_api_url(endpoint)
        d = data or {}
        d.setdefault("format", "json")
        resp = self._client.post(url, data=d)
        resp.raise_for_status()
        if not resp.text.strip():
            return []
        ct = resp.headers.get("content-type", "")
        if "json" in ct:
            return resp.json()
        return []

    # --- Collections ---

    def get_collections(self) -> list[CollectionInfo]:
        raw = self._get("getCollectionValuesAndCounts")
        return [
            CollectionInfo(
                collection=item.get("collection", ""),
                count=int(item.get("count", 0)),
                authorized=bool(int(item.get("Authorized", 1))),
            )
            for item in raw
        ]

    def get_collection_names(self) -> list[str]:
        raw = self._get("getCollectionValues")
        return [item.get("collection", "") for item in raw]

    def get_collection_details(self, collection: str | None = None) -> list[CollectionDetail]:
        params: dict[str, Any] = {}
        if collection:
            params["collectionName"] = collection
        raw = self._get("getCollectionDescriptions", params)
        return [
            CollectionDetail(
                collection_name=item.get("collectionName", ""),
                description=item.get("description", ""),
                description_uri=item.get("descriptionURI", ""),
                id=int(item.get("id", 0)),
            )
            for item in raw
        ]

    # --- Patients ---

    def get_patients(self, collection: str, patient_id: str | None = None) -> list[PatientInfo]:
        params: dict[str, Any] = {"Collection": collection}
        if patient_id:
            params["PatientId"] = patient_id
        raw = self._get("getPatient", params)
        return [
            PatientInfo(
                patient_id=item.get("PatientId", ""),
                patient_name=item.get("PatientName", ""),
                patient_sex=item.get("PatientSex", ""),
                patient_birth_date=item.get("PatientBirthDate", ""),
                collection=item.get("Collection", collection),
                species=item.get("SpeciesDescription", ""),
                phantom=self._parse_phantom(item.get("Phantom", "NO")),
            )
            for item in raw
        ]

    def get_patients_by_modality(
        self, collection: str, modality: str
    ) -> list[PatientInfo]:
        params = {"Collection": collection, "Modality": modality}
        raw = self._get("getPatientByCollectionAndModality", params)
        return [
            PatientInfo(patient_id=item.get("PatientId", ""), collection=collection)
            for item in raw
        ]

    @staticmethod
    def _parse_phantom(val: str) -> bool:
        if isinstance(val, str):
            return val.upper() in ("YES", "TRUE", "1")
        return bool(val)

    # --- Studies ---

    def get_studies(
        self,
        collection: str,
        patient_id: str | None = None,
        study_uid: str | None = None,
    ) -> list[StudyInfo]:
        params: dict[str, Any] = {"Collection": collection}
        if patient_id:
            params["PatientId"] = patient_id
        if study_uid:
            params["StudyInstanceUID"] = study_uid
        raw = self._get("getPatientStudy", params)
        return [
            StudyInfo(
                study_instance_uid=item.get("StudyInstanceUID", ""),
                study_date=item.get("StudyDate", ""),
                study_description=item.get("StudyDescription", ""),
                study_id=item.get("StudyID", ""),
                collection=item.get("Collection", collection),
                patient_id=item.get("PatientId", patient_id or ""),
                patient_name=item.get("PatientName", ""),
                patient_sex=item.get("PatientSex", ""),
                patient_age=item.get("PatientAge", ""),
                series_count=int(item.get("SeriesCount", 0)),
            )
            for item in raw
        ]

    # --- Series ---

    def get_series(
        self,
        collection: str,
        patient_id: str | None = None,
        study_uid: str | None = None,
    ) -> list[SeriesInfo]:
        params: dict[str, Any] = {"Collection": collection}
        if patient_id:
            params["PatientId"] = patient_id
        if study_uid:
            params["StudyInstanceUID"] = study_uid
        raw = self._get("getSeries", params)
        return [
            SeriesInfo(
                series_instance_uid=item.get("SeriesInstanceUID", "")
                or item.get("SeriesUID", ""),
                series_description=item.get("SeriesDescription", ""),
                series_date=item.get("SeriesDate", ""),
                series_number=item.get("SeriesNumber", ""),
                modality=item.get("Modality", ""),
                collection=item.get("Collection", collection),
                patient_id=item.get("PatientId", patient_id or ""),
                study_instance_uid=item.get("StudyInstanceUID", study_uid or ""),
                body_part_examined=item.get("BodyPartExamined", ""),
                manufacturer=item.get("Manufacturer", ""),
                slice_thickness=self._parse_float(item.get("SliceThickness")),
                pixel_spacing=item.get("PixelSpacing", ""),
                num_images=int(item.get("NumberImages", 0) or item.get("ImageCount", 0)),
            )
            for item in raw
        ]

    def get_series_size(self, series_uid: str) -> SeriesSize:
        raw = self._get("getSeriesSize", {"SeriesInstanceUID": series_uid})
        if raw:
            item = raw[0] if isinstance(raw, list) else raw
            return SeriesSize(
                series_instance_uid=item.get("SeriesInstanceUID", series_uid),
                series_size=int(item.get("SeriesSize", 0)),
                image_count=int(item.get("ImageCount", 0)),
            )
        return SeriesSize(series_instance_uid=series_uid)

    def get_dicom_tags(self, series_uid: str) -> list[DicomTag]:
        raw = self._get("getDicomTags", {"SeriesUID": series_uid})
        return [
            DicomTag(
                element=item.get("element", ""),
                name=item.get("name", ""),
                data=item.get("data", ""),
            )
            for item in raw
        ]

    # --- Downloads ---

    def download_series(self, series_uid: str) -> bytes:
        url = self.settings.get_api_url("getImage")
        params = {"SeriesInstanceUID": series_uid}
        resp = self._client.get(url, params=params)
        resp.raise_for_status()
        return resp.content

    # --- Utilities ---

    def get_body_part_counts(
        self, collection: str | None = None, modality: str | None = None
    ) -> list[BodyPartCount]:
        params: dict[str, Any] = {}
        if collection:
            params["Collection"] = collection
        if modality:
            params["Modality"] = modality
        raw = self._get("getBodyPartValuesAndCounts", params)
        return [
            BodyPartCount(
                body_part=item.get("bodyPart", ""),
                count=int(item.get("count", 0)),
                authorized=bool(int(item.get("Authorized", 1))),
            )
            for item in raw
        ]

    def get_modality_counts(
        self, collection: str | None = None, body_part: str | None = None
    ) -> list[ModalityCount]:
        params: dict[str, Any] = {}
        if collection:
            params["Collection"] = collection
        if body_part:
            params["BodyPartExamined"] = body_part
        raw = self._get("getModalityValuesAndCounts", params)
        return [
            ModalityCount(
                modality=item.get("modality", ""),
                count=int(item.get("count", 0)),
                authorized=bool(int(item.get("Authorized", 1))),
            )
            for item in raw
        ]

    def get_manufacturer_counts(
        self,
        collection: str | None = None,
        modality: str | None = None,
        body_part: str | None = None,
    ) -> list[ManufacturerCount]:
        params: dict[str, Any] = {}
        if collection:
            params["Collection"] = collection
        if modality:
            params["Modality"] = modality
        if body_part:
            params["BodyPartExamined"] = body_part
        raw = self._get("getManufacturerValuesAndCounts", params)
        return [
            ManufacturerCount(
                manufacturer=item.get("manufacturer", ""),
                count=int(item.get("count", 0)),
                authorized=bool(int(item.get("Authorized", 1))),
            )
            for item in raw
        ]

    @staticmethod
    def _parse_float(val: Any) -> float | None:
        if val is None:
            return None
        try:
            return float(val)
        except (ValueError, TypeError):
            return None
