# Setup guide

Step-by-step instructions for setting up beestgraph on a Raspberry Pi 5 from bare metal to a running system.

## Table of contents

- [Prerequisites](#prerequisites)
- [1. Raspberry Pi OS](#1-raspberry-pi-os)
- [2. NVMe SSD](#2-nvme-ssd)
- [3. System packages](#3-system-packages)
- [4. Docker](#4-docker)
- [5. Python and uv](#5-python-and-uv)
- [6. Node.js](#6-nodejs)
- [7. Tailscale](#7-tailscale)
- [8. Syncthing](#8-syncthing)
- [9. Clone and configure beestgraph](#9-clone-and-configure-beestgraph)
- [10. Start services](#10-start-services)
- [11. Claude Code](#11-claude-code)
- [12. Verify installation](#12-verify-installation)

---

## Prerequisites

- Raspberry Pi 5 (16GB recommended, 8GB minimum)
- NVMe SSD (M.2 2230 or 2242 via HAT)
- MicroSD card (for initial OS flash, 16GB+)
- Ethernet or Wi-Fi connection
- keep.md account (Plus plan, $10/mo)

---

## 1. Raspberry Pi OS

Flash Raspberry Pi OS (64-bit, Bookworm) using the [Raspberry Pi Imager](https://www.raspberrypi.com/software/).

In the imager settings, configure:
- Hostname (e.g., `beestgraph`)
- SSH access (enable with password or SSH key)
- Wi-Fi credentials (if not using Ethernet)
- Locale and timezone

Boot the Pi and SSH in:

```bash
ssh pi@beestgraph.local
```

Update the system:

```bash
sudo apt update && sudo apt upgrade -y
sudo reboot
```

---

## 2. NVMe SSD

If you have an NVMe HAT installed, enable PCIe Gen 3 for maximum throughput:

```bash
sudo nano /boot/firmware/config.txt
```

Add this line:

```
dtparam=pciex1_gen=3
```

Reboot and verify the NVMe drive is detected:

```bash
sudo reboot
lsblk
# You should see nvme0n1
```

Format and mount the drive (adjust device name if different):

```bash
sudo mkfs.ext4 /dev/nvme0n1p1
sudo mkdir -p /mnt/nvme
sudo mount /dev/nvme0n1p1 /mnt/nvme

# Make it persistent
echo '/dev/nvme0n1p1 /mnt/nvme ext4 defaults,noatime 0 2' | sudo tee -a /etc/fstab
```

Create the working directories:

```bash
sudo mkdir -p /mnt/nvme/dev /mnt/nvme/vault /mnt/nvme/docker
sudo chown -R $USER:$USER /mnt/nvme/dev /mnt/nvme/vault
```

---

## 3. System packages

Install essential build tools and libraries:

```bash
sudo apt install -y \
  build-essential \
  git \
  curl \
  wget \
  graphviz \
  jq \
  htop
```

---

## 4. Docker

Install Docker using the official convenience script:

```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh
```

Add your user to the Docker group (log out and back in after):

```bash
sudo usermod -aG docker $USER
```

Optionally, move Docker's data directory to the NVMe drive for better performance:

```bash
sudo systemctl stop docker
sudo mkdir -p /mnt/nvme/docker
sudo rsync -aP /var/lib/docker/ /mnt/nvme/docker/

# Configure Docker to use the new location
sudo tee /etc/docker/daemon.json <<EOF
{
  "data-root": "/mnt/nvme/docker"
}
EOF

sudo systemctl start docker
```

Verify Docker works:

```bash
docker run --rm hello-world
```

---

## 5. Python and uv

Raspberry Pi OS Bookworm ships with Python 3.11. Verify:

```bash
python3 --version
# Python 3.11.x
```

Install [uv](https://docs.astral.sh/uv/), the fast Python package manager:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Add uv to your shell path (restart your shell or source the profile):

```bash
source $HOME/.local/bin/env
uv --version
```

---

## 6. Node.js

Install Node.js 20 LTS via NodeSource:

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

Verify:

```bash
node --version
# v20.x.x
npm --version
```

---

## 7. Tailscale

Install Tailscale for secure remote access:

```bash
curl -fsSL https://tailscale.com/install.sh | sh
sudo tailscale up
```

Follow the authentication URL printed in the terminal. Once connected, your Pi is accessible via its Tailscale hostname from any device on your tailnet.

Optional: enable Tailscale SSH for passwordless access:

```bash
sudo tailscale up --ssh
```

---

## 8. Syncthing

Install Syncthing for peer-to-peer vault sync:

```bash
sudo apt install -y syncthing
```

Enable and start the Syncthing service:

```bash
sudo systemctl enable syncthing@$USER
sudo systemctl start syncthing@$USER
```

Access the Syncthing web UI at `http://localhost:8384` (or via Tailscale). Configure it to sync your vault directory (`/mnt/nvme/vault` or `~/vault`) with your other devices.

---

## 9. Clone and configure beestgraph

```bash
cd /mnt/nvme/dev
git clone https://github.com/terbeest/beestgraph.git
cd beestgraph
```

Copy configuration templates:

```bash
cp config/beestgraph.yml.example config/beestgraph.yml
cp docker/.env.example docker/.env
```

Edit `docker/.env` with your API keys:

```bash
nano docker/.env
```

Required values:

```bash
VAULT_PATH=/mnt/nvme/vault      # Path to your Obsidian vault
```

Optional values:

```bash
TELEGRAM_BOT_TOKEN=...          # If using Telegram bot
TELEGRAM_ALLOWED_USERS=12345    # Your Telegram user ID
KEEPMD_API_KEY=...              # If using keep.md REST API
```

Edit `config/beestgraph.yml` with your preferences (see [`docs/configuration.md`](configuration.md) for all options).

Install Python dependencies:

```bash
make install
```

Install web UI dependencies:

```bash
make web-install
```

---

## 10. Start services

Start FalkorDB:

```bash
make docker-up
```

Wait for containers to be healthy (check with `docker ps`). Then initialize the graph schema:

```bash
make init-schema
```

Start the processing pipeline:

```bash
# Start the vault watchdog and Telegram bot
make run-all

# Or start individual services
make run-watcher   # Vault inbox watchdog
make run-bot       # Telegram bot
```

Set up the keep.md cron job (runs every 15 minutes):

```bash
crontab -e
```

Add this line:

```
*/15 * * * * cd /mnt/nvme/dev/beestgraph && make run-poller >> /tmp/beestgraph-poller.log 2>&1
```

---

## 11. Claude Code

Install Claude Code following the [official instructions](https://docs.anthropic.com/en/docs/claude-code). On ARM64:

```bash
# Install via npm
npm install -g @anthropic-ai/claude-code
```

Configure the MCP servers:

```bash
chmod +x scripts/configure-mcp.sh
./scripts/configure-mcp.sh
```

This writes the MCP server configuration to `~/.claude/mcp.json` based on `config/mcp.json.example`.

---

## 12. Verify installation

Run these checks to confirm everything is working:

```bash
# Docker containers are healthy
docker ps

# FalkorDB responds to queries
docker exec beestgraph-falkordb redis-cli PING
# Expected: PONG

# Python pipeline can import
uv run python -c "import src; print('Pipeline OK')"

# Linter passes
make lint

# Tests pass
make test

# FalkorDB Browser is accessible
# Open http://localhost:3000 in a browser (or via Tailscale hostname)
```

---

## Next steps

- Set up keep.md sources: see [`docs/keepmd-integration.md`](keepmd-integration.md)
- Configure Obsidian vault: see [`docs/obsidian-integration.md`](obsidian-integration.md)
- Review the graph schema: see [`docs/schema.md`](schema.md)
- Troubleshoot issues: see [`docs/troubleshooting.md`](troubleshooting.md)
