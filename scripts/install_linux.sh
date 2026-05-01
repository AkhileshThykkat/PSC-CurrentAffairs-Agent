#!/bin/bash
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo ""
    echo -e "${GREEN}============================================${NC}"
    echo -e "${GREEN}  PSC Current Affairs Agent - Linux Setup${NC}"
    echo -e "${GREEN}============================================${NC}"
    echo ""
}

print_step() {
    echo -e "${BLUE}[$1] $2${NC}"
}

print_success() {
    echo -e "${GREEN}  $1${NC}"
}

print_warn() {
    echo -e "${YELLOW}  WARNING: $1${NC}"
}

print_error() {
    echo -e "${RED}  ERROR: $1${NC}"
}

print_header

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$INSTALL_DIR")"
cd "$PROJECT_DIR"

INSTALL_MODE="native"

if [ "$1" == "--docker" ] || [ "$1" == "-d" ]; then
    INSTALL_MODE="docker"
    echo -e "${YELLOW}Docker mode selected. Running docker-start.sh...${NC}"
    exec bash scripts/docker-start.sh
fi

echo "Install mode: ${INSTALL_MODE}"
echo "Project dir: ${PROJECT_DIR}"
echo ""

# --- Step 1: Detect OS and package manager ---
print_step "1" "Detecting system"

if command -v apt &> /dev/null; then
    PKG_MANAGER="apt"
    OS_NAME="Debian/Ubuntu"
elif command -v dnf &> /dev/null; then
    PKG_MANAGER="dnf"
    OS_NAME="Fedora/RHEL"
elif command -v pacman &> /dev/null; then
    PKG_MANAGER="pacman"
    OS_NAME="Arch Linux"
else
    print_warn "Unknown package manager. You may need to install dependencies manually."
    PKG_MANAGER="unknown"
    OS_NAME="Unknown"
fi

echo "  OS: $OS_NAME"
echo "  Package manager: $PKG_MANAGER"

# --- Step 2: Install system dependencies ---
print_step "2" "Installing system dependencies"

install_package_apt() {
    if [ "$(id -u)" -eq 0 ]; then
        apt-get update && apt-get install -y "$1"
    else
        if sudo -n true 2>/dev/null; then
            sudo apt-get update && sudo apt-get install -y "$1"
        else
            print_warn "Need sudo to install packages. You will be prompted."
            sudo apt-get update && sudo apt-get install -y "$1"
        fi
    fi
}

install_package_dnf() {
    if [ "$(id -u)" -eq 0 ]; then
        dnf install -y "$1"
    else
        sudo dnf install -y "$1"
    fi
}

install_package_pacman() {
    if [ "$(id -u)" -eq 0 ]; then
        pacman -Sy --noconfirm "$1"
    else
        sudo pacman -Sy --noconfirm "$1"
    fi
}

install_package() {
    case $PKG_MANAGER in
        apt) install_package_apt "$1" ;;
        dnf) install_package_dnf "$1" ;;
        pacman) install_package_pacman "$1" ;;
        *) print_error "Cannot install $1 automatically. Install it manually." ;;
    esac
}

if command -v git &> /dev/null; then
    print_success "git already installed"
else
    echo "  Installing git..."
    install_package git
fi

if command -v redis-server &> /dev/null; then
    print_success "redis already installed"
else
    echo "  Installing redis..."
    install_package redis-server
    echo "  Starting redis..."
    if [ "$(id -u)" -eq 0 ]; then
        systemctl enable --now redis 2>/dev/null || systemctl enable --now redis-server 2>/dev/null || true
    else
        sudo systemctl enable --now redis 2>/dev/null || sudo systemctl enable --now redis-server 2>/dev/null || true
    fi
    if redis-cli ping 2>/dev/null | grep -q PONG; then
        print_success "redis is running"
    else
        print_warn "redis may not have started. Try: sudo systemctl start redis-server"
    fi
fi

if command -v curl &> /dev/null; then
    print_success "curl already installed"
else
    echo "  Installing curl..."
    install_package curl
fi

if command -v build-essential &> /dev/null || command -v gcc &> /dev/null; then
    print_success "build tools already installed"
else
    echo "  Installing build tools..."
    case $PKG_MANAGER in
        apt) install_package "build-essential" ;;
        dnf) install_package "@development-tools" ;;
        pacman) install_package "base-devel" ;;
    esac
fi

# --- Step 3: Install uv (user scope) ---
print_step "3" "Installing uv (Python package manager)"

if command -v uv &> /dev/null; then
    print_success "uv already installed: $(uv --version)"
else
    echo "  Installing uv to user scope (~/.local/bin)..."
    curl -LsSf https://astral.sh/uv/install.sh | sh

    if [ -d "$HOME/.local/bin" ]; then
        if ! echo "$PATH" | grep -q "$HOME/.local/bin"; then
            echo "  Adding ~/.local/bin to PATH..."
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.profile" 2>/dev/null || true
            export PATH="$HOME/.local/bin:$PATH"
        fi
    fi

    if command -v uv &> /dev/null; then
        print_success "uv installed: $(uv --version)"
    else
        print_error "uv installation failed. Try: curl -LsSf https://astral.sh/uv/install.sh | sh"
        exit 1
    fi
fi

# --- Step 4: Install Python dependencies ---
print_step "4" "Installing Python dependencies"

uv sync --no-dev
print_success "Dependencies installed"

# --- Step 5: Install Ollama ---
print_step "5" "Setting up Ollama (local AI)"

if command -v ollama &> /dev/null; then
    print_success "ollama already installed"
else
    echo "  Installing Ollama..."
    curl -fsSL https://ollama.com/install.sh | sh
    print_success "Ollama installed"
fi

if pgrep -x ollama > /dev/null 2>&1; then
    print_success "Ollama is running"
else
    echo "  Starting Ollama service..."
    if [ "$(id -u)" -eq 0 ]; then
        systemctl enable --now ollama 2>/dev/null || true
    else
        sudo systemctl enable --now ollama 2>/dev/null || true
    fi

    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        print_success "Ollama is running"
    else
        print_warn "Ollama may not be running. Start with: ollama serve"
    fi
fi

# --- Step 6: Pull AI model ---
print_step "6" "Downloading AI model (gemma:2b, ~1.5 GB)"

if curl -s http://localhost:11434/api/tags | grep -q "gemma:2b" 2>/dev/null; then
    print_success "gemma:2b model already downloaded"
else
    echo "  Pulling gemma:2b... (this takes a few minutes)"
    ollama pull gemma:2b
    print_success "Model downloaded"
fi

# --- Step 7: Initialize database ---
print_step "7" "Initializing database"

uv run python scripts/init_db.py
print_success "Database initialized"

# --- Step 8: Create systemd user services (optional) ---
print_step "8" "Setting up background services"

echo ""
echo "  Would you like to set up systemd user services?"
echo "  This will auto-start the API server and Celery worker in the background."
echo "  (Redis and Ollama are already system services)"
echo ""
read -p "  Set up background services? [y/N]: " setup_services

if [[ "$setup_services" =~ ^[Yy]$ ]]; then
    mkdir -p "$HOME/.config/systemd/user"

    cat > "$HOME/.config/systemd/user/psc-agent-api.service" << 'EOF'
[Unit]
Description=PSC Current Affairs Agent API
After=network.target redis.service ollama.service

[Service]
Type=simple
WorkingDirectory=%h/Documents/Learning/current_affairs_scrapper
ExecStart=%h/.local/bin/uv run uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=always
RestartSec=10
Environment=HOME=%h

[Install]
WantedBy=default.target
EOF

    cat > "$HOME/.config/systemd/user/psc-agent-worker.service" << 'EOF'
[Unit]
Description=PSC Current Affairs Agent Celery Worker
After=network.target redis.service ollama.service

[Service]
Type=simple
WorkingDirectory=%h/Documents/Learning/current_affairs_scrapper
ExecStart=%h/.local/bin/uv run celery -A app.workers.celery_app worker --loglevel=info
Restart=always
RestartSec=10
Environment=HOME=%h

[Install]
WantedBy=default.target
EOF

    cat > "$HOME/.config/systemd/user/psc-agent-beat.service" << 'EOF'
[Unit]
Description=PSC Current Affairs Agent Celery Beat
After=network.target redis.service

[Service]
Type=simple
WorkingDirectory=%h/Documents/Learning/current_affairs_scrapper
ExecStart=%h/.local/bin/uv run celery -A app.workers.celery_app beat --loglevel=info
Restart=always
RestartSec=10
Environment=HOME=%h

[Install]
WantedBy=default.target
EOF

    # Fix the working directory to the actual project path
    sed -i "s|%h/Documents/Learning/current_affairs_scrapper|$PROJECT_DIR|g" "$HOME/.config/systemd/user/psc-agent-api.service"
    sed -i "s|%h/Documents/Learning/current_affairs_scrapper|$PROJECT_DIR|g" "$HOME/.config/systemd/user/psc-agent-worker.service"
    sed -i "s|%h/Documents/Learning/current_affairs_scrapper|$PROJECT_DIR|g" "$HOME/.config/systemd/user/psc-agent-beat.service"

    systemctl --user daemon-reload
    systemctl --user enable --now psc-agent-api
    systemctl --user enable --now psc-agent-worker
    systemctl --user enable --now psc-agent-beat

    print_success "Background services enabled and started"
    echo ""
    echo "  Manage services with:"
    echo "    systemctl --user status psc-agent-api"
    echo "    systemctl --user status psc-agent-worker"
    echo "    systemctl --user status psc-agent-beat"
    echo "    systemctl --user restart psc-agent-api"
else
    print_warn "Skipping background services setup"
    echo ""
    echo "  To start manually, open 3 terminals and run:"
    echo "    Terminal 1: uv run uvicorn app.main:app --reload --port 8000"
    echo "    Terminal 2: uv run celery -A app.workers.celery_app worker --loglevel=info"
    echo "    Terminal 3: uv run celery -A app.workers.celery_app beat --loglevel=info"
fi

# --- Done ---
echo ""
echo -e "${GREEN}============================================${NC}"
echo -e "${GREEN}  Setup Complete!${NC}"
echo -e "${GREEN}============================================${NC}"
echo ""
echo "  App: http://localhost:8000"
echo "  Docs: cat INSTRUCTIONS.md"
echo ""
echo "  Quick commands:"
echo "    Run pipeline now:  uv run python scripts/run_pipeline.py"
echo "    Start services:    uv run uvicorn app.main:app --reload --port 8000"
echo "    View logs:         tail -f logs/*.log (if configured)"
echo "    Run tests:         uv run pytest tests/ -v"
echo ""
