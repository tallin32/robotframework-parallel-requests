# Release Process

## Versioning

This project uses PEP 440-compatible versions.

Examples:

- Development: `0.1.0.dev1`
- Release candidate: `1.0.0rc1`
- Final: `1.0.0`

## Tagging

Use `v` + package version for release tags:

- `v0.1.0.dev1`
- `v1.0.0rc1`
- `v1.0.0`

## CI/CD behavior

- Dev and prerelease tags publish to TestPyPI.
- RC and final tags publish to PyPI.
- Workflow classification is controlled by `.github/workflows/publish.yml`.
