# 🤝 Contributing to Universal Video Downloader

First off — **thank you** for considering a contribution! 🎉 Every bit helps, from fixing typos to shipping features.

## 📑 Contents

- [Code of Conduct](#code-of-conduct)
- [Ways to contribute](#ways-to-contribute)
- [Development setup](#development-setup)
- [Development workflow](#development-workflow)
- [Coding standards](#coding-standards)
- [Testing](#testing)
- [Commit messages](#commit-messages)
- [Pull requests](#pull-requests)
- [Reporting bugs](#reporting-bugs)
- [Requesting features](#requesting-features)
- [License](#license)

---

## Code of Conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold it. Be kind. 🙏

---

## Ways to contribute

- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🧪 Add tests
- 🌍 Add/refine translations (`frontend/localization/`)
- 🔧 Fix issues labeled [`good first issue`](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/labels/good%20first%20issue)

---

## Development setup

```bash
git clone https://github.com/YOUR_USERNAME/Universal_Video_Downloader.git
cd Universal_Video_Downloader
python3.13 -m venv .venv
source .venv/bin/activate            # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env
python scripts/run_dev.py
```

See **[docs/INSTALL.md](docs/INSTALL.md)** for OS-specific steps.

---

## Development workflow

```mermaid
flowchart LR
    A[Fork] --> B[Branch] --> C[Code + tests] --> D[ruff + pytest] --> E[Push] --> F[Open PR] --> G[Review] --> H[Merge]
```

1. **Fork** the repo and create a branch: `git checkout -b feature/my-feature`
2. Make focused changes with tests
3. Run the quality gate locally (below)
4. Push and open a Pull Request against `master`

---

## Coding standards

- **Python 3.13+**, full **type annotations**
- **Async** where appropriate; never block the event loop (yt-dlp runs in a thread)
- Keep changes focused and minimal; follow existing structure and naming
- No raw yt-dlp exceptions to clients — use `DownloaderError` subclasses
- Don't add narration comments; explain *why*, not *what*

```bash
ruff check backend tests      # lint
ruff format backend tests     # format (optional)
mypy backend                  # types (best-effort)
```

---

## Testing

```bash
pytest -q                                   # fast
pytest --cov=backend --cov-report=term-missing -v   # with coverage
```

- Add tests for new behavior (unit / api / integration)
- Keep the suite green; CI runs ruff + pytest on every push/PR

---

## Commit messages

Use clear, imperative messages. [Conventional Commits](https://www.conventionalcommits.org/) are encouraged:

```
feat: add playlist download support
fix: handle Rutube 404 by bumping yt-dlp
docs: expand cookie troubleshooting
test: cover cookie fallback ordering
```

---

## Pull requests

- Fill out the PR template completely
- Link related issues (`Closes #123`)
- Ensure **CI passes** (lint + tests)
- Update docs when behavior changes
- One logical change per PR when possible

---

## Reporting bugs

Open a [Bug Report](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/issues/new?template=bug_report.yml) with:
- Steps to reproduce, expected vs actual
- Versions (Python, yt-dlp, FFmpeg, OS/Docker)
- Redacted logs (never paste your `cookies.txt` or secrets)

---

## Requesting features

Open a [Feature Request](https://github.com/PatvakanGasparyan/Universal_Video_Downloader/issues/new?template=feature_request.yml) describing the problem and proposed solution.

---

## License

By contributing, you agree that your contributions are licensed under the **[MIT License](LICENSE)**.
