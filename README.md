# Squigit Packages

This repository hosts signed Linux package repositories for Squigit sidecar engines.

- APT repo root: `apt/`
- DNF repo root: `rpm/`
- Public signing key: `keys/squigit-packages.asc`

Each lane mirrors the latest installable `.deb` / `.rpm` payload alongside signed metadata so package managers can install directly. Release assets are also published in `squigit-org/squigit` for archival distribution.

## APT (Debian/Ubuntu)

1. Add repository + key:

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://squigit-org.github.io/squigit-packages/keys/squigit-packages.asc | \
  gpg --dearmor | sudo tee /etc/apt/keyrings/squigit-packages.gpg >/dev/null
echo "deb [signed-by=/etc/apt/keyrings/squigit-packages.gpg] https://squigit-org.github.io/squigit-packages/apt stable ocr stt" | \
  sudo tee /etc/apt/sources.list.d/squigit-packages.list >/dev/null
```

2. Update package cache:

```bash
sudo apt update
```

3. Install package:

```bash
sudo apt install squigit-ocr squigit-stt
```

## DNF (Fedora/RHEL)

1. Add repository file:

```bash
sudo curl -fsSL https://squigit-org.github.io/squigit-packages/rpm/squigit.repo \
  -o /etc/yum.repos.d/squigit.repo
```

2. Update package cache:

```bash
sudo dnf makecache
```

3. Install package:

```bash
sudo dnf install squigit-ocr squigit-stt
```
