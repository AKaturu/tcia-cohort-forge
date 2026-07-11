from __future__ import annotations

import io
import os
import shutil
import stat
import zipfile
from pathlib import Path, PurePosixPath, PureWindowsPath

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.models import CohortManifest, DownloadResult, SeriesInfo


class CohortDownloader:
    def __init__(self, client: NbiaClient | None = None) -> None:
        self._owns_client = client is None
        self.client = client or NbiaClient()

    def close(self) -> None:
        if self._owns_client:
            self.client.close()

    def __enter__(self) -> CohortDownloader:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()

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
                result.total_bytes += (
                    s.estimated_size_bytes if hasattr(s, "estimated_size_bytes") else 0
                )
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
                result.errors.append(f"Series {s.series_instance_uid}: {e}")

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
            result.errors.append(f"Series {series_info.series_instance_uid}: {e}")

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
        try:
            with zipfile.ZipFile(io.BytesIO(data)) as zf:
                members = _validated_zip_members(zf, Path(target_dir))
                for member, destination in members:
                    if member.is_dir():
                        destination.mkdir(parents=True, exist_ok=True)
                        continue
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    with zf.open(member) as source, destination.open("wb") as output:
                        shutil.copyfileobj(source, output)
                return sum(not member.is_dir() for member, _ in members)
        except zipfile.BadZipFile:
            dcm_dir = os.path.join(target_dir, "dicom")
            os.makedirs(dcm_dir, exist_ok=True)
            ext = ".dcm"
            out_path = os.path.join(dcm_dir, f"image{ext}")
            with open(out_path, "wb") as f:
                f.write(data)
            return 1


def _sanitize(name: str) -> str:
    return "".join(c if c.isalnum() or c in "_- " else "_" for c in name).strip()


def _validated_zip_members(
    archive: zipfile.ZipFile, target_dir: Path
) -> list[tuple[zipfile.ZipInfo, Path]]:
    """Validate every member before extraction to prevent path traversal."""
    root = target_dir.resolve()
    validated: list[tuple[zipfile.ZipInfo, Path]] = []
    for member in archive.infolist():
        raw_name = member.filename.replace("\\", "/")
        relative = PurePosixPath(raw_name)
        if (
            not raw_name
            or relative.is_absolute()
            or PureWindowsPath(raw_name).is_absolute()
            or ".." in relative.parts
        ):
            raise ValueError(f"Unsafe ZIP member path: {member.filename!r}")
        if relative.name.startswith("."):
            continue

        mode = member.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise ValueError(f"ZIP symbolic links are not supported: {member.filename!r}")

        destination = (root / Path(*relative.parts)).resolve()
        try:
            destination.relative_to(root)
        except ValueError as exc:
            raise ValueError(f"Unsafe ZIP member path: {member.filename!r}") from exc
        validated.append((member, destination))
    return validated
