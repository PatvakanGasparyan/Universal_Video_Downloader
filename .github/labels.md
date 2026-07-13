# 🏷️ Issue & PR Labels

A suggested label taxonomy for this repository. Create these under
**Settings → Labels**, or apply them with the [GitHub CLI](https://cli.github.com/):

```bash
gh label create "bug"              --color d73a4a --description "Something isn't working"
gh label create "enhancement"      --color a2eeef --description "New feature or request"
gh label create "documentation"    --color 0075ca --description "Docs improvements"
gh label create "good first issue" --color 7057ff --description "Good for newcomers"
gh label create "help wanted"      --color 008672 --description "Extra attention is wanted"
gh label create "triage"           --color fbca04 --description "Needs triage"
gh label create "dependencies"     --color 0366d6 --description "Dependency updates"
gh label create "ci"               --color 000000 --description "CI/CD"
gh label create "docker"           --color 2496ed --description "Docker/containers"
gh label create "python"           --color 3776ab --description "Python code"
gh label create "cookies"          --color c2a000 --description "Cookie/auth related"
gh label create "yt-dlp"           --color ff0000 --description "Extractor / yt-dlp"
gh label create "wontfix"          --color ffffff --description "Will not be worked on"
gh label create "duplicate"        --color cfd3d7 --description "Already exists"
gh label create "question"         --color d876e3 --description "Further info requested"
gh label create "security"         --color b60205 --description "Security related"
```

## Label groups

| Group | Labels |
|-------|--------|
| **Type** | `bug`, `enhancement`, `documentation`, `question` |
| **Status** | `triage`, `help wanted`, `good first issue`, `wontfix`, `duplicate` |
| **Area** | `docker`, `python`, `cookies`, `yt-dlp`, `ci`, `security` |
| **Automation** | `dependencies` |
