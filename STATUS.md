# tcia-cohort-forge — Project Status

## Current Release

**v0.1.0** — Initial release providing a CLI tool to query, browse, and download patient cohorts from The Cancer Imaging Archive (TCIA) via the NBIA v4 REST API.

## Implemented Features

- 8 Typer commands: collections, patients, studies, series, search, download, download-cohort, info
- NBIA v4 API client (NbiaClient) covering all endpoints
- CohortBuilder for high-level cohort construction from criteria
- CohortDownloader with automatic DICOM extraction and organized directory layout
- CSV/JSON export for collections, patients, studies, series, and cohort manifests
- Configurable via environment variables (TCIA_API_BASE_URL, TCIA_AUTH_TOKEN, TCIA_OUTPUT_DIR, TCIA_TIMEOUT)
- Reproducible public-workflow demo media generation
- 13 Pydantic models

## Quality Gates

- 51 tests across 6 files — all passing on Python 3.11 and 3.12
- No ruff violations
- No mypy errors (8 source files)
- CI: GitHub Actions green on both versions

## Known Issues

- None at this release
