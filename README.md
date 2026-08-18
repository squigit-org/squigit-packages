# Squigit Packages

Signed APT and DNF metadata for Squigit Linux sidecar packages.

## Install on Debian-based Linux

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://squigit-org.github.io/squigit-distribution/keys/squigit-distribution.asc | gpg --dearmor | sudo tee /etc/apt/keyrings/squigit-distribution.gpg >/dev/null
echo "deb [signed-by=/etc/apt/keyrings/squigit-distribution.gpg] https://github.com/squigit-org/squigit-distribution/raw/main/apt stable ocr cli" | sudo tee /etc/apt/sources.list.d/squigit-distribution.list >/dev/null
sudo apt-get update
sudo apt-get install -y squigit-ocr squigit-cli
```

## Install on RPM-based Linux

```bash
sudo curl -fsSL https://squigit-org.github.io/squigit-distribution/rpm/squigit.repo -o /etc/yum.repos.d/squigit.repo
sudo dnf makecache --refresh
sudo dnf install -y squigit-ocr squigit-cli
```

## Repo Contents

- APT metadata root: `apt/`
- DNF metadata root: `rpm/`
- Public key: `keys/squigit-distribution.asc`
- Current Debian package filenames/tags are tracked in `metadata/package-assets.env`
- Package binaries are served from `squigit-org/squigit` GitHub Releases.
