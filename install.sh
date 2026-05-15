#!/usr/bin/env bash
set -euo pipefail

# ── Colors ──────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── Root check ──────────────────────────────────────────────────────────
if [ "$EUID" -ne 0 ]; then
    warn "Not running as root. Docker commands may require sudo."
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Docker ──────────────────────────────────────────────────────────────
if command -v docker &>/dev/null; then
    ok "Docker found: $(docker --version)"
else
    warn "Docker not found — installing..."
    curl -fsSL https://get.docker.com | sh
    ok "Docker installed: $(docker --version)"
fi

# ── Docker Compose ──────────────────────────────────────────────────────
if docker compose version &>/dev/null; then
    ok "Docker Compose found: $(docker compose version --short)"
else
    warn "Docker Compose not found — installing..."
    DOCKER_CONFIG=${DOCKER_CONFIG:-$HOME/.docker/cli-plugins}
    mkdir -p "$DOCKER_CONFIG"
    curl -SL "https://github.com/docker/compose/releases/latest/download/docker-compose-linux-$(uname -m)" \
        -o "$DOCKER_CONFIG/docker-compose"
    chmod +x "$DOCKER_CONFIG/docker-compose"
    ok "Docker Compose installed: $(docker compose version --short)"
fi

# ── Directories ─────────────────────────────────────────────────────────
mkdir -p data logs
ok "Directories ready: data/, logs/"

# ── .env ────────────────────────────────────────────────────────────────
if [ ! -f backend/.env ]; then
    if [ -f backend/.env.example ]; then
        cp backend/.env.example backend/.env
        ok "Created backend/.env from .env.example"
    else
        warn "No .env.example found — you will need to create backend/.env manually"
    fi
else
    ok "backend/.env already exists"
fi

# ── Build & Start ───────────────────────────────────────────────────────
info "Building and starting containers..."
docker compose up -d --build
ok "Containers started"

# ── Wait for health ────────────────────────────────────────────────────
info "Waiting for backend to be ready..."
PORT="${PORT:-8080}"
for i in $(seq 1 30); do
    if curl -sf "http://localhost:${PORT}/health" &>/dev/null; then
        ok "Backend is healthy!"
        break
    fi
    if [ "$i" -eq 30 ]; then
        warn "Backend did not become healthy within 30s. Check logs: docker compose logs backend"
    fi
    sleep 1
done

# ── Public IP ───────────────────────────────────────────────────────────
PUBLIC_IP=""
for url in "https://api.ipify.org" "https://ifconfig.me" "https://icanhazip.com"; do
    PUBLIC_IP=$(curl -sf --max-time 5 "$url" 2>/dev/null || true)
    if [ -n "$PUBLIC_IP" ]; then
        break
    fi
done

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║${NC}  copywrAIter installed successfully!              ${GREEN}║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════╝${NC}"
echo ""

if [ -n "$PUBLIC_IP" ]; then
    info "Setup Wizard: http://${PUBLIC_IP}:${PORT}"
else
    info "Setup Wizard: http://localhost:${PORT}"
    info "If on a VPS, find your public IP and visit http://<IP>:${PORT}"
fi

echo ""
info "Next steps:"
echo "  1. Open the Setup Wizard URL above"
echo "  2. Configure your AI provider (OpenAI / Anthropic / Hermes-compatible)"
echo "  3. Set up Repliz API for distribution"
echo "  4. Start creating content!"
echo ""
info "Local development (without Docker):"
echo "  curl -LsSf https://astral.sh/uv/install.sh | sh"
echo "  cd backend && uv venv && source .venv/bin/activate"
echo "  uv pip install -r requirements.txt"
echo "  uv run uvicorn main:app --reload --port 8080"
echo ""
info "Manage containers:"
echo "  docker compose logs -f     # View logs"
echo "  docker compose restart     # Restart"
echo "  docker compose down        # Stop"
