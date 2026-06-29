from __future__ import annotations

from pydantic import BaseModel, Field


class CollectionInfo(BaseModel):
    collection: str
    count: int = 0
    authorized: bool = True


class CollectionDetail(BaseModel):
    collection_name: str
    description: str = ""
    description_uri: str = ""
    id: int = 0


class PatientInfo(BaseModel):
    patient_id: str
    patient_name: str = ""
    patient_sex: str = ""
    patient_birth_date: str = ""
    collection: str = ""
    species: str = ""
    phantom: bool = False


class StudyInfo(BaseModel):
    study_instance_uid: str
    study_date: str = ""
    study_description: str = ""
    study_id: str = ""
    collection: str = ""
    patient_id: str = ""
    patient_name: str = ""
    patient_sex: str = ""
    patient_age: str = ""
    series_count: int = 0


class SeriesInfo(BaseModel):
    series_instance_uid: str
    series_description: str = ""
    series_date: str = ""
    series_number: str = ""
    modality: str = ""
    collection: str = ""
    patient_id: str = ""
    study_instance_uid: str = ""
    body_part_examined: str = ""
    manufacturer: str = ""
    slice_thickness: float | None = None
    pixel_spacing: str = ""
    num_images: int = 0
    series_size: int = 0


class SeriesSize(BaseModel):
    series_instance_uid: str
    series_size: int = 0
    image_count: int = 0


class DicomTag(BaseModel):
    element: str = ""
    name: str = ""
    data: str = ""


class BodyPartCount(BaseModel):
    body_part: str
    count: int = 0
    authorized: bool = True


class ModalityCount(BaseModel):
    modality: str
    count: int = 0
    authorized: bool = True


class ManufacturerCount(BaseModel):
    manufacturer: str
    count: int = 0
    authorized: bool = True


class CohortCriteria(BaseModel):
    collection: str | None = None
    modalities: list[str] = Field(default_factory=list)
    body_parts: list[str] = Field(default_factory=list)
    patient_ids: list[str] = Field(default_factory=list)
    study_uids: list[str] = Field(default_factory=list)
    series_uids: list[str] = Field(default_factory=list)



class CohortManifest(BaseModel):
    criteria: CohortCriteria = Field(default_factory=CohortCriteria)
    collections: list[str] = Field(default_factory=list)
    patients: list[PatientInfo] = Field(default_factory=list)
    studies: list[StudyInfo] = Field(default_factory=list)
    series: list[SeriesInfo] = Field(default_factory=list)
    total_patients: int = 0
    total_studies: int = 0
    total_series: int = 0


class DownloadResult(BaseModel):
    output_dir: str
    total_series: int = 0
    total_files: int = 0
    total_bytes: int = 0
    errors: list[str] = Field(default_factory=list)
