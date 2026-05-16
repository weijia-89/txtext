# Changelog

All notable changes to this project are documented here.

## [Unreleased]

### Added

- `SECURITY.md`: threat model, trust boundaries, secrets and supply-chain notes, reporting.
- `CHANGELOG.md` for release notes.

### Changed

- `reference/link-detection.py`: only `http`/`https` hrefs; max URL length; reject control chars in URLs.
- `reference/content-extraction.py`: stricter URL argv validation (length, control chars); clearer scheme error (no URL echo to stderr).
