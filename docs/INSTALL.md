# 📥 Installation Guide

Complete, copy-pasteable setup instructions for every platform.

> [!TIP]
> The fastest path is [Docker](#-docker). Native installs are great for development.

## 📑 Contents

- [Prerequisites](#prerequisites)
- [Ubuntu / Debian](#-ubuntu--debian)
- [Other Linux (Fedora / Arch)](#-other-linux)
- [Windows](#-windows)
- [macOS](#-macos)
- [Docker](#-docker)
- [Verify the installation](#-verify-the-installation)
- [Updating](#-updating)
- [Uninstall](#-uninstall)

---

## Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | **3.13+** | Backend runtime |
| FFmpeg | latest | Merging & audio conversion |
| Git | any | Cloning the repo |
| yt-dlp | ≥ 2025.6.9 | Installed via `pip` automatically |

---

## 🐧 Ubuntu / Debian

```bash
# 1. System packages
sudo apt update
sudo apt install -y python3.13 python3.13-venv python3-pip ffmpeg git

# 2. Clone
git clone https://github.com/PatvakanGasparyan/Universal_Video_Downloader.git
cd Universal_Video_Downloader

# 3. Virtual environment
python3.13 -m venv .venv
source .venv/bin/activate

# 4. Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Environment
cp .env.example .env

# 6. Run
python scripts/run_dev.py
```

> If `python3.13` is unavailable, add the deadsnakes PPA:
> `sudo add-apt-repository ppa:deadsnakes/ppa && sudo apt update`

---

## 🐧 Other Linux

<details>
<summary><b>Fedora / RHEL</b></summary>

```bash
sudo dnf install -y python3.13 ffmpeg git
git clone https://github.com/PatvakanGasparyan/Universal_Video_Downloader.git
cd Universal_Video_Downloader
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python scripts/run_dev.py
```

</details>

<details>
<summary><b>Arch Linux</b></summary>

```bash
sudo pacman -S python ffmpeg git
git clone https://github.com/PatvakanGasparyan/Universal_Video_Downloader.git
cd Universal_Video_Downloader
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt && cp .env.example .env
python scripts/run_dev.py
```

</details>

---

## 🪟 Windows

```powershell
# 1. Install tooling (PowerShell as your user)
winget install Python.Python.3.13
winget install Gyan.FFmpeg
winget install Git.Git

# 2. Clone
git clone https://github.com/PatvakanGasparyan/Universal_Video_Downloader.git
cd Universal_Video_Downloader

# 3. Virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# 4. Dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 5. Environment + run
Copy-Item .env.example .env
python scripts/run_dev.py
```

> [!NOTE]
> If PowerShell blocks activation, run:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

---

## 🍎 macOS

```bash
# 1. Homebrew packages
brew install python@3.13 ffmpeg git

# 2. Clone + setup
git clone https://github.com/PatvakanGasparyan/Universal_Video_Downloader.git
cd Universal_Video_Downloader
python3.13 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env

# 3. Run
python scripts/run_dev.py
```

---

## 🐳 Docker

```bash
git clone https://github.com/PatvakanGasparyan/Universal_Video_Downloader.git
cd Universal_Video_Downloader
cp .env.example .env
docker compose up -d --build
```

Full Docker reference: **[DOCKER.md](DOCKER.md)**.

---

## ✅ Verify the installation

```bash
curl http://localhost:8000/api/health
# {"status":"healthy"}
```

Then open **http://localhost:8000** in your browser.

---

## 🔄 Updating

```bash
git pull
pip install -r requirements.txt   # native
# or
docker compose up -d --build      # docker

# Keep extractors fresh
pip install -U yt-dlp
```

---

## 🧹 Uninstall

```bash
# Native
deactivate 2>/dev/null; rm -rf .venv

# Docker
docker compose down -v   # -v also removes volumes (deletes data!)
```
