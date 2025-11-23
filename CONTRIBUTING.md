Thank you for considering contributing!

This project follows a fork → pull request workflow for public contributions.
If you are an internal team member and will contribute frequently, contact the
maintainer about collaborator access.

Quickstart (fork → PR)

1. Fork the repository on GitHub.
2. Clone your fork and add upstream:

```powershell
git clone git@github.com:your-username/robotframework-parallel-requests.git
cd robotframework-parallel-requests
git remote add upstream git@github.com:tallin32/robotframework-parallel-requests.git
```

3. Create a branch and set up the dev environment:

```powershell
git checkout -b feature/short-description
python -m venv .venv
. .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

4. Run tests and linters locally before opening a PR:

```powershell
pytest tests/ -v
```

5. Push your branch and open a pull request against `tallin32:main`.

Branch naming

- Use `feature/`, `fix/`, or `docs/` prefixes, e.g. `feature/add-rate-limit`.

PR expectations

- Provide a clear description of the change and why it is needed.
- Include testing steps and results.
- Update `README.md` or other docs for any API changes.
- Add unit tests for new behavior where appropriate.

Review process

- At least one approving review is required before merging.
- CI must pass on the branch before the PR can be merged.

Code of conduct

This repository follows a standard Code of Conduct. Be respectful and constructive.

Thank you — contributions are appreciated!
