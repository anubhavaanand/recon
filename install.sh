#!/usr/bin/env bash
set -euo pipefail

REPO="anubhavanand/recon"
BRANCH="main"
INSTALL_DIR="${HOME}/.local/share/recon"

# ── Colors ──
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}RECON — Terminal-native patent research tool${NC}"
echo ""

# ── Check Python ──
if ! command -v python3 &>/dev/null; then
    echo -e "${RED}ERR: Python 3.12+ is required but python3 not found.${NC}"
    echo "Action: Install Python from https://python.org or your package manager."
    exit 1
fi

PY_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
PY_MAJOR=$(echo "$PY_VERSION" | cut -d. -f1)
PY_MINOR=$(echo "$PY_VERSION" | cut -d. -f2)

if [ "$PY_MAJOR" -lt 3 ] || { [ "$PY_MAJOR" -eq 3 ] && [ "$PY_MINOR" -lt 12 ]; }; then
    echo -e "${RED}ERR: Python 3.12+ required (found $PY_VERSION).${NC}"
    echo "Action: Upgrade Python and try again."
    exit 1
fi

echo -e "${GREEN}✓${NC} Python $PY_VERSION found"

# ── Prefer pipx, fall back to pip ──
if command -v pipx &>/dev/null; then
    echo -e "${CYAN}Installing via pipx...${NC}"
    
    # Install from GitHub
    pipx install "git+https://github.com/${REPO}.git@${BRANCH}" || {
        echo -e "${RED}ERR: pipx install failed.${NC}"
        echo "Action: Check network connectivity or install manually:"
        echo "  git clone https://github.com/${REPO}.git"
        echo "  cd recon && pip install ."
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✓ RECON installed successfully via pipx${NC}"
    echo ""
    echo "Run:  recon search --help"
    echo "Or:   recon            (launches interactive TUI)"

elif command -v pip3 &>/dev/null; then
    echo -e "${CYAN}Installing via pip3 to ${INSTALL_DIR}...${NC}"
    
    mkdir -p "$INSTALL_DIR"
    
    if [ -d "${INSTALL_DIR}/.git" ]; then
        echo "Updating existing clone..."
        cd "$INSTALL_DIR" && git pull origin "$BRANCH"
    else
        echo "Cloning repository..."
        git clone --depth 1 --branch "$BRANCH" "https://github.com/${REPO}.git" "$INSTALL_DIR"
    fi
    
    pip3 install --user -e "$INSTALL_DIR" || {
        echo -e "${RED}ERR: pip install failed.${NC}"
        echo "Action: Check dependencies or install manually:"
        echo "  pip install --user -e ${INSTALL_DIR}"
        exit 1
    }
    
    echo ""
    echo -e "${GREEN}✓ RECON installed successfully${NC}"
    echo ""
    echo "Make sure ~/.local/bin is in your PATH."
    echo "Run:  recon search --help"
    echo "Or:   recon            (launches interactive TUI)"
else
    echo -e "${RED}ERR: Neither pipx nor pip3 found.${NC}"
    echo "Action: Install Python with pip:"
    echo "  https://pip.pypa.io/en/stable/installation/"
    exit 1
fi
