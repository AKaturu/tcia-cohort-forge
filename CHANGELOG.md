# Changelog

## Unreleased

- Correct manifest `StudyDate` values by joining series to study metadata
- Deduplicate patients, studies, and series returned through overlapping filters
- Reject path traversal and symbolic links before extracting downloaded archives
- Close NBIA HTTP clients deterministically in API and CLI workflows
- Add command-level tests for all eight CLI commands

## v0.1.0 (2026-06-28)

- Initial release with NBIA v4 REST API client
- CLI commands: collections, patients, studies, series, search, download, download-cohort, info
- CohortBuilder and CohortDownloader with organized output layout
- CSV/JSON export for all data types
- Environment-variable configuration
- Reproducible demo media generation
