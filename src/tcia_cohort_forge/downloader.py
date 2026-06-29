from __future__ import annotations

import io
import os
import zipfile
from pathlib import Path

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.models import CohortManifest, DownloadResult, SeriesInfo


class CohortDownloader:
    def __init__(self, client: NbiaClient | None = None) -> None:
        self.client = client or NbiaClient()

    def download_manifest(
        self,
        manifest: CohortManifest,
        output_dir: str = "downloads",
        dry_run: bool = False,
    ) -> DownloadResult:
        result = DownloadResult(output_dir=os.path.abspath(output_dir))

        for s in manifest.series:
            if dry_run:
                result.total_series += 1
                result.total_bytes += s.estimated_size_bytes if hasattr(s, 'estimated_size_bytes') else 0
                continue

            try:
                series_dir = self._series_output_dir(output_dir, s)
                os.makedirs(series_dir, exist_ok=True)

                zip_data = self.client.download_series(s.series_instance_uid)
                files_written = self._extract_zip(zip_data, series_dir)
                result.total_files += files_written
                result.total_series += 1
                result.total_bytes += len(zip_data)
            except Exception as e:
                result.errors.append(
                    f"Series {s.series_instance_uid}: {e}"
                )

        return result

    def download_series(
        self,
        series_info: SeriesInfo,
        output_dir: str = "downloads",
    ) -> DownloadResult:
        result = DownloadResult(output_dir=os.path.abspath(output_dir))

        try:
            series_dir = self._series_output_dir(output_dir, series_info)
            os.makedirs(series_dir, exist_ok=True)

            zip_data = self.client.download_series(series_info.series_instance_uid)
            files_written = self._extract_zip(zip_data, series_dir)
            result.total_files += files_written
            result.total_series += 1
            result.total_bytes += len(zip_data)
        except Exception as e:
            result.errors.append(
                f"Series {series_info.series_instance_uid}: {e}"
            )

        return result

    @staticmethod
    def _series_output_dir(base: str, s: SeriesInfo) -> str:
        parts = [base]
        if s.collection:
            parts.append(_sanitize(s.collection))
        if s.patient_id:
            parts.append(_sanitize(s.patient_id))
        if s.study_instance_uid:
            parts.append(s.study_instance_uid[-12:])
        parts.append(s.series_instance_uid)
        return os.path.join(*parts)

    @staticmethod
    def _extract_zip(data: bytes, target_dir: str) -> int:
        count = 0
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                for member in zf.namelist():
                    path = Path(member)
                    if path.name.startswith("."):
                        continue
                    zf.extract(member, target_dir)
                    count += 1
        except zipfile.BadZipFile:
            dcm_dir = os.path.join(target_dir, "dicom")
            os.makedirs(dcm_dir, exist_ok=True)
            ext = ".dcm"
            out_path = os.path.join(dcm_dir, f"image{ext}")
            with open(out_path, "wb") as f:
                f.write(data)
            count = 1
        return count


def _sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in "_- " else "_" for c in name).strip()
