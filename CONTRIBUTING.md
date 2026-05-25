# Contributing

Thanks for considering contributing to `robotframework-parallel-requests`!

We aim for a clean, well‑tested, and well‑documented library. This guide outlines the workflow and expectations for pull requests.

## Ways to Contribute
- Bug reports and edge case scenarios
- Feature requests (retry strategies, async transport, observability)
- Documentation improvements (README examples, advanced recipes)
- Test coverage additions
- Performance / profiling investigations

## Development Setup
```bash
git clone git@github.com:tallin32/robotframework-parallel-requests.git
cd robotframework-parallel-requests
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Running Tests
```bash
pytest -v
robot examples/parallel_requests.robot
```
Run both Python unit tests and Robot example suites before opening a PR.

## Branching & Workflow
1. Fork (or create a feature branch if you are a collaborator).
2. Create a descriptive branch name: `feature/retry-jitter`, `fix/race-condition-worker-shutdown`, `docs/release-process`.
3. Make focused changes; avoid unrelated refactors.
4. Update or add tests relevant to your change.
5. Update `CHANGELOG.md` if the public API/behavior changes.
6. Open a Pull Request targeting `main`.

## Pull Request Checklist
- [ ] CHANGELOG updated (if applicable)
- [ ] Added/updated tests
- [ ] All tests passing locally (`pytest`, `robot` examples)
- [ ] Docstrings added/updated for new keywords or public API
- [ ] README / documentation updated if user-facing behavior changed
- [ ] No unrelated formatting-only changes

## Coding Standards
- Python 3.8+ compatible syntax
- Keep functions short and purposeful
- Prefer explicit names over abbreviations
- Avoid one-letter variable names (except counters like `i`)
- Graceful error handling; raise clear exceptions

## Testing Guidelines
- Use `respx` for httpx request mocking
- Test success, failure (exceptions), and edge cases (timeouts, retries)
- Keep test names descriptive; one behavior per test
- Verify new keyword exposure via library instance when adding features

## Documentation Style
- Keyword docstrings follow: `Parallel Keyword Name    arg1    arg2=default` line + explanation + examples.
- Use reST compatible formatting for libdoc rendering (no heavy Markdown tables inside docstrings).

## Performance Considerations
For performance-related changes:
- Provide before/after timing metrics
- Ensure no regression in correctness or test flakiness
- Document trade-offs clearly in the PR description

## Communication
- Use GitHub Issues for feature requests & bugs
- Link issues in PRs (`Closes #XX` when appropriate)
- Keep PR scope minimal; large changes can be split

## Release Impact
If your change affects publishing:
- Note any required updates to release workflow
- Confirm tag strategy (e.g. will require a minor version bump if backward incompatible)

## Security
If you discover a security issue:
- Do **not** open a public issue initially
- Email the maintainer or open a private advisory (GitHub Security Advisories)

## License
By contributing you agree your contributions are under the MIT License.

## Questions?
Open an issue titled `Question:` with a concise summary.

Thanks again for helping improve the project!
