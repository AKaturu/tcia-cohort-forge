# tcia-cohort-forge — Project State

## Status: Complete

A CLI tool to query, browse, and download patient cohorts from The Cancer Imaging Archive (TCIA) via the NBIA v4 REST API.

## What's Built

### Source (`src/tcia_cohort_forge/`)
- **models.py** — Pydantic models: CollectionInfo, CollectionDetail, PatientInfo, StudyInfo, SeriesInfo, SeriesSize, DicomTag, BodyPartCount, ModalityCount, ManufacturerCount, CohortCriteria, CohortManifest, DownloadResult (13 models)
- **config.py** — Settings dataclass with env var overrides (TCIA_API_BASE_URL, TCIA_AUTH_TOKEN, TCIA_OUTPUT_DIR, TCIA_TIMEOUT)
- **client.py** — NbiaClient wrapping all NBIA v4 endpoints: collections, patients, studies, series, downloads, DICOM tags, body parts, modalities, manufacturers
- **cohort.py** — CohortBuilder: high-level cohort construction from criteria (collection, modalities, body parts, patient IDs)
- **downloader.py** — CohortDownloader: DICOM ZIP download with automatic extraction, organized Collection/PatientID/StudyUID/SeriesUID directory layout
- **exporter.py** — CSV/JSON export for collections, patients, studies, series, and cohort manifests
- **cli.py** — 8 Typer commands: collections, patients, studies, series, search, download, download-cohort, info

### Tests (`tests/`)
- 51 tests across 6 files (models, client, cohort, config, downloader, exporter)
- All passing on Python 3.11 and 3.12

### Validation
- ruff: clean
- mypy: 0 errors (8 source files)
- CI: GitHub Actions (ruff → mypy → pytest → help command) green on both versions

### Delivery
- GitHub: https://github.com/AKaturu/tcia-cohort-forge
- MIT License
- `tcia-cohort-forge` CLI entry point
- Public TCIA API by default, configurable base URL + auth token

## CLI Commands

| Command | Description |
|---------|-------------|
| `collections` | List all TCIA collections with patient counts |
| `patients <collection>` | List patients in a collection |
| `studies <collection>` | List studies in a collection |
| `series <collection>` | List DICOM series in a collection |
| `search <collection> [--modality] [--body-part]` | Build a cohort with criteria |
| `download <series-uid>` | Download a single DICOM series |
| `download-cohort <manifest.json>` | Download all series in a cohort manifest |
| `info <collection>` | Show collection summary statistics |

## No Known Issues
- All tests pass
- No mypy errors
- No ruff violations
- CI green on 3.11 and 3.12
