import os
import tempfile
import zipfile
from io import BytesIO
from unittest.mock import MagicMock

import pytest

from tcia_cohort_forge.client import NbiaClient
from tcia_cohort_forge.downloader import CohortDownloader
from tcia_cohort_forge.models import CohortCriteria, CohortManifest, SeriesInfo


@pytest.fixture
def mock_client() -> MagicMock:
    return MagicMock(spec=NbiaClient)


@pytest.fixture
def downloader(mock_client: MagicMock) -> CohortDownloader:
    return CohortDownloader(client=mock_client)


def test_download_series(downloader: CohortDownloader, mock_client: MagicMock):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("image-1.dcm", b"dicom-data-1")
        zf.writestr("image-2.dcm", b"dicom-data-2")
    zip_buffer.seek(0)
    mock_client.download_series.return_value = zip_buffer.read()

    with tempfile.TemporaryDirectory() as tmpdir:
        info = SeriesInfo(
            series_instance_uid="1.2.3.4.5",
            collection="TEST",
            patient_id="P001",
            study_instance_uid="STUDY-UID",
        )
        result = downloader.download_series(info, output_dir=tmpdir)
        assert result.total_files == 2
        assert result.total_series == 1
        assert result.errors == []


def test_download_series_dry_run(downloader: CohortDownloader, mock_client: MagicMock):
    manifest = CohortManifest(
        criteria=CohortCriteria(collection="TEST"),
        series=[SeriesInfo(series_instance_uid="1.2.3.4")],
        total_series=1,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = downloader.download_manifest(manifest, output_dir=tmpdir, dry_run=True)
        assert result.total_series == 1
        mock_client.download_series.assert_not_called()


def test_download_series_network_error(downloader: CohortDownloader, mock_client: MagicMock):
    mock_client.download_series.side_effect = Exception("Connection error")

    with tempfile.TemporaryDirectory() as tmpdir:
        info = SeriesInfo(series_instance_uid="1.2.3.4", patient_id="P1")
        result = downloader.download_series(info, output_dir=tmpdir)
        assert result.total_files == 0
        assert len(result.errors) == 1
        assert "Connection error" in result.errors[0]


def test_download_manifest(downloader: CohortDownloader, mock_client: MagicMock):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("img.dcm", b"data")
    zip_buffer.seek(0)
    mock_client.download_series.return_value = zip_buffer.read()

    manifest = CohortManifest(
        criteria=CohortCriteria(collection="TEST"),
        series=[
            SeriesInfo(series_instance_uid="S1", patient_id="P1", collection="TEST"),
            SeriesInfo(series_instance_uid="S2", patient_id="P1", collection="TEST"),
        ],
        total_series=2,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        result = downloader.download_manifest(manifest, output_dir=tmpdir)
        assert result.total_series == 2
        assert result.total_files >= 2


def test_extract_zip(downloader: CohortDownloader):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("file1.dcm", b"data1")
        zf.writestr("file2.dcm", b"data2")
    zip_buffer.seek(0)

    with tempfile.TemporaryDirectory() as tmpdir:
        count = CohortDownloader._extract_zip(zip_buffer.read(), tmpdir)
        assert count == 2
        assert os.path.exists(os.path.join(tmpdir, "file1.dcm"))
        assert os.path.exists(os.path.join(tmpdir, "file2.dcm"))


def test_extract_non_zip_fallback(downloader: CohortDownloader):
    with tempfile.TemporaryDirectory() as tmpdir:
        count = CohortDownloader._extract_zip(b"not-a-zip", tmpdir)
        assert count == 1
        dcm_dir = os.path.join(tmpdir, "dicom")
        files = os.listdir(dcm_dir)
        assert len(files) == 1


@pytest.mark.parametrize("member", ["../outside.dcm", "nested/../../outside.dcm", "C:/outside.dcm"])
def test_extract_zip_rejects_path_traversal(tmp_path, member: str):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr(member, b"not-safe")

    with pytest.raises(ValueError, match="Unsafe ZIP member path"):
        CohortDownloader._extract_zip(zip_buffer.getvalue(), str(tmp_path / "target"))

    assert not (tmp_path / "outside.dcm").exists()


def test_extract_zip_validates_all_members_before_writing(tmp_path):
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zf:
        zf.writestr("safe.dcm", b"safe")
        zf.writestr("../outside.dcm", b"not-safe")

    target = tmp_path / "target"
    with pytest.raises(ValueError, match="Unsafe ZIP member path"):
        CohortDownloader._extract_zip(zip_buffer.getvalue(), str(target))

    assert not (target / "safe.dcm").exists()
