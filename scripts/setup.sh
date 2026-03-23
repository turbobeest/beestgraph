#!/usr/bin/env bash
# beestgraph/scripts/setup.sh — Full Raspberry Pi 5 setup
# Run as: sudo ./scripts/setup.sh
set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()  { echo -e "${GREEN}[beestgraph]${NC} $*"; }
warn() { echo -e "${YELLOW}[beestgraph]${NC} $*"; }

# ── Pre-flight checks ───────────────────────────────────────
if [[ $EUID -ne 0 ]]; then
    echo "This script must be run as root (sudo)." >&2
    exit 1
fi

REAL_USER="${SUDO_USER:-$(whoami)}"
REAL_HOME=$(eval echo "~${REAL_USER}")

log "Setting up beestgraph for user: ${REAL_USER}"
log "Home directory: ${REAL_HOME}"

# ── System updates ───────────────────────────────────────────
log "Updating system packages..."
apt-get update -qq
apt-get upgrade -y -qq

# ── Install system dependencies ──────────────────────────────
log "Installing system dependencies..."
apt-get install -y -qq \
    git \
    curl \
    wget \
    build-essential \
    python3 \
    python3-pip \
    python3-venv \
    graphviz \
    jq \
    tmux \
    mosh \
    htop \
    unattended-upgrades

# ── Enable PCIe Gen 3 for NVMe performance ──────────────────
CONFIG_FILE="/boot/firmware/config.txt"
if ! grep -q "dtparam=pciex1_gen=3" "$CONFIG_FILE" 2>/dev/null; then
    log "Enabling PCIe Gen 3 for NVMe..."
    echo "dtparam=pciex1_gen=3" >> "$CONFIG_FILE"
    warn "Reboot required for PCIe Gen 3 to take effect."
fi

# ── Install Docker ───────────────────────────────────────────
if ! command -v docker &>/dev/null; then
    log "Installing Docker..."
    curl -fsSL https://get.docker.com | sh
    usermod -aG docker "$REAL_USER"
    systemctl enable docker
    systemctl start docker
    log "Docker installed. User ${REAL_USER} added to docker group."
else
    log "Docker already installed."
fi

# ── Install Docker Compose plugin ────────────────────────────
if ! docker compose version &>/dev/null; then
    log "Installing Docker Compose plugin..."
    apt-get install -y -qq docker-compose-plugin
else
    log "Docker Compose already installed."
fi

# ── Install Tailscale ────────────────────────────────────────
if ! command -v tailscale &>/dev/null; then
    log "Installing Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    log "Tailscale installed. Run 'sudo tailscale up' to authenticate."
else
    log "Tailscale already installed."
fi

# ── Install Node.js (LTS) via NodeSource ─────────────────────
if ! command -v node &>/dev/null; then
    log "Installing Node.js LTS..."
    curl -fsSL https://deb.nodesource.com/setup_22.x | bash -
    apt-get install -y -qq nodejs
else
    log "Node.js already installed: $(node --version)"
fi

# ── Install uv (Python package manager) ─────────────────────
if ! command -v uv &>/dev/null; then
    log "Installing uv..."
    sudo -u "$REAL_USER" curl -LsSf https://astral.sh/uv/install.sh | sudo -u "$REAL_USER" sh
else
    log "uv already installed."
fi

# ── Create vault directory structure ─────────────────────────
VAULT_PATH="${REAL_HOME}/vault"
log "Creating vault directory structure at ${VAULT_PATH}..."
sudo -u "$REAL_USER" mkdir -p \
    "${VAULT_PATH}/inbox" \
    "${VAULT_PATH}/knowledge/technology" \
    "${VAULT_PATH}/knowledge/science" \
    "${VAULT_PATH}/knowledge/business" \
    "${VAULT_PATH}/knowledge/culture" \
    "${VAULT_PATH}/knowledge/health" \
    "${VAULT_PATH}/knowledge/personal" \
    "${VAULT_PATH}/knowledge/meta" \
    "${VAULT_PATH}/projects" \
    "${VAULT_PATH}/areas" \
    "${VAULT_PATH}/resources" \
    "${VAULT_PATH}/archives" \
    "${VAULT_PATH}/templates"

# ── Create project directory ─────────────────────────────────
PROJECT_DIR="${REAL_HOME}/beestgraph"
log "Ensuring project directory exists at ${PROJECT_DIR}..."
sudo -u "$REAL_USER" mkdir -p "${PROJECT_DIR}"

# ── Copy config templates ────────────────────────────────────
if [[ -f "${PROJECT_DIR}/docker/.env.example" ]] && [[ ! -f "${PROJECT_DIR}/docker/.env" ]]; then
    log "Copying .env.example to .env — edit with your API keys."
    sudo -u "$REAL_USER" cp "${PROJECT_DIR}/docker/.env.example" "${PROJECT_DIR}/docker/.env"
fi

if [[ -f "${PROJECT_DIR}/config/beestgraph.yml.example" ]] && [[ ! -f "${PROJECT_DIR}/config/beestgraph.yml" ]]; then
    sudo -u "$REAL_USER" cp "${PROJECT_DIR}/config/beestgraph.yml.example" "${PROJECT_DIR}/config/beestgraph.yml"
fi

# ── Summary ──────────────────────────────────────────────────
echo ""
log "${BOLD}Setup complete!${NC}"
echo ""
echo "  Next steps:"
echo "  1. Reboot if PCIe Gen 3 was just enabled"
echo "  2. Run:  sudo tailscale up --ssh"
echo "  3. Edit: ${PROJECT_DIR}/docker/.env  (add API keys)"
echo "  4. Run:  ./scripts/install-claude-code.sh"
echo "  5. Run:  cd docker && docker compose up -d"
echo "  6. Run:  ./scripts/configure-mcp.sh"
echo "  7. Run:  ./scripts/init-schema.sh"
echo ""
