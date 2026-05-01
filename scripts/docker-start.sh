#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}PSC Current Affairs Agent - Docker Setup${NC}"
echo "============================================="

check_prerequisites() {
    if ! command -v docker &> /dev/null; then
        echo -e "${RED}Error: docker is not installed.${NC}"
        echo "Install it with: curl -fsSL https://get.docker.com | sh"
        echo ""
        echo "Or run the native install instead: bash scripts/install_linux.sh"
        exit 1
    fi

    if ! docker info &> /dev/null; then
        echo -e "${RED}Error: Docker is not running or you don't have permission.${NC}"
        echo "Try: sudo systemctl start docker"
        echo "Or add your user to the docker group: sudo usermod -aG docker \$USER"
        exit 1
    fi

    if ! command -v docker compose &> /dev/null; then
        echo -e "${RED}Error: docker compose plugin is not installed.${NC}"
        echo "Install it with: sudo apt-get install docker-compose-plugin"
        exit 1
    fi

    echo -e "${GREEN}Prerequisites OK${NC}"
}

setup_env() {
    if [ ! -f .env ]; then
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo -e "${GREEN}.env file created.${NC}"
    else
        echo -e "${YELLOW}.env already exists, skipping.${NC}"
    fi
}

pull_model() {
    echo ""
    echo -e "${YELLOW}Starting Ollama container to pull the AI model (this may take a few minutes)...${NC}"
    echo "Model: gemma:2b (~1.5 GB)"

    docker compose up -d ollama

    echo "Waiting for Ollama to start..."
    until curl -s http://localhost:11434/api/tags > /dev/null 2>&1; do
        sleep 3
    done

    echo "Pulling gemma:2b model..."
    docker exec $(docker compose ps -q ollama) ollama pull gemma:2b

    echo -e "${GREEN}Model downloaded successfully.${NC}"
}

start_services() {
    echo ""
    echo -e "${GREEN}Starting all services...${NC}"
    docker compose up -d

    echo ""
    echo "Waiting for services to be ready..."
    sleep 5

    echo ""
    echo -e "${GREEN}Services running:${NC}"
    docker compose ps

    echo ""
    echo -e "${GREEN}App is available at: http://localhost:8000${NC}"
    echo ""
    echo "Useful commands:"
    echo "  View logs:          docker compose logs -f"
    echo "  Stop services:      docker compose down"
    echo "  Restart services:   docker compose restart"
    echo "  Rebuild:            docker compose up -d --build"
    echo "  Run pipeline now:   docker compose exec worker python scripts/run_pipeline.py"
}

show_menu() {
    echo ""
    echo "What would you like to do?"
    echo "  1) Full setup (pull model + start services)"
    echo "  2) Start services only (model already pulled)"
    echo "  3) Stop all services"
    echo "  4) View logs"
    echo "  5) Rebuild and restart"
    echo "  6) Trigger pipeline now"
    echo "  0) Exit"
    echo ""
    read -p "Choose an option [1-6, 0]: " choice

    case $choice in
        1)
            check_prerequisites
            setup_env
            pull_model
            start_services
            ;;
        2)
            check_prerequisites
            docker compose up -d
            echo -e "${GREEN}Services started. http://localhost:8000${NC}"
            ;;
        3)
            docker compose down
            echo -e "${GREEN}Services stopped.${NC}"
            ;;
        4)
            docker compose logs -f
            ;;
        5)
            docker compose up -d --build
            echo -e "${GREEN}Rebuilt and restarted.${NC}"
            ;;
        6)
            docker compose exec worker python scripts/run_pipeline.py
            ;;
        0)
            echo "Exiting."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option.${NC}"
            show_menu
            ;;
    esac
}

if [ "$1" == "--non-interactive" ] || [ "$1" == "-y" ]; then
    check_prerequisites
    setup_env
    pull_model
    start_services
else
    check_prerequisites
    setup_env
    show_menu
fi
