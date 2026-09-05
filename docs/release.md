# Release Process

## Versioning

This project uses PEP 440-compatible versions.

Examples:

- Development: `0.1.0.dev2`
- Release candidate: `1.0.0rc1`
- Final: `1.0.0`

## Tagging

Use `v` + package version for release tags:

- `v0.1.0.dev2`
- `v1.0.0rc1`
- `v1.0.0`

Ensure `pyproject.toml` `version` matches the tag before pushing.

## CI/CD behavior

- Dev and prerelease tags publish to TestPyPI.
- RC and final tags publish to PyPI.
- Workflow classification is controlled by `.github/workflows/publish.yml`.

## Trusted publishing setup

PyPI/TestPyPI trusted publishers need the **workflow file name** (not the workflow `name:`):

- Workflow file: `publish.yml`
- GitHub environments: `testpypi` (dev/alpha/beta/rc) and `pypi` (rc/final)

For a `v*.*.*.devN` tag such as `v0.1.0.dev2`, only the `testpypi` environment is required.
Add the `pypi` environment before the first RC or final tag.

## Dev release checklist

1. Bump `version` in `pyproject.toml`.
2. Update `CHANGELOG.md`.
3. Run tests: `pytest tests/ -v`.
4. Commit and merge to `main`.
5. Tag and push: `git tag v0.1.0.dev2 && git push origin v0.1.0.dev2`.
6. Confirm the Publish workflow succeeds, then validate install from TestPyPI.
