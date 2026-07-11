# Changelog

## Unreleased

- Reported optional series-size lookup failures instead of silently suppressing them.
- Correct manifest `StudyDate` values by joining series to study metadata
- Deduplicate patients, studies, and series returned through overlapping filters
- Reject path traversal and symbolic links before extracting downloaded archives
- Close NBIA HTTP clients deterministically in API and CLI workflows
- Add command-level tests for all eight CLI commands
- Publish PEP 561 typing metadata and remove blanket mypy import suppression
- Add Python 3.13 CI coverage and modern SPDX package metadata

## v0.1.0 (2026-06-28)

- Initial release with NBIA v4 REST API client
- CLI commands: collections, patients, studies, series, search, download, download-cohort, info
- CohortBuilder and CohortDownloader with organized output layout
- CSV/JSON export for all data types
- Environment-variable configuration
- Reproducible demo media generation
