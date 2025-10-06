#!/bin/bash
# SWE-bench Environment Setup Script (Fixed for Ubuntu/Debian)
# This script creates a Python virtual environment and installs all dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}SWE-bench Environment Setup${NC}"
echo -e "${GREEN}================================${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: pyproject.toml not found${NC}"
    echo "Please run this script from the swebench-end2end directory"
    exit 1
fi

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3.12 &> /dev/null; then
    PYTHON_CMD="python3.12"
    PYTHON_VENV_PKG="python3.12-venv"
    echo -e "${GREEN}✓ Found Python 3.12${NC}"
elif command -v python3.11 &> /dev/null; then
    PYTHON_CMD="python3.11"
    PYTHON_VENV_PKG="python3.11-venv"
    echo -e "${GREEN}✓ Found Python 3.11${NC}"
elif command -v python3.10 &> /dev/null; then
    PYTHON_CMD="python3.10"
    PYTHON_VENV_PKG="python3.10-venv"
    echo -e "${GREEN}✓ Found Python 3.10${NC}"
else
    echo -e "${RED}Error: Python 3.10+ not found${NC}"
    echo "Please install Python 3.10 or higher"
    exit 1
fi

echo "Using: $PYTHON_CMD ($($PYTHON_CMD --version))"
echo ""

# Check if python3-venv is installed
echo -e "${YELLOW}Checking for python3-venv package...${NC}"
if ! dpkg -l | grep -q "^ii  $PYTHON_VENV_PKG"; then
    echo -e "${RED}✗ $PYTHON_VENV_PKG is not installed${NC}"
    echo ""
    echo -e "${YELLOW}To install it, run:${NC}"
    echo -e "${BLUE}    sudo apt update${NC}"
    echo -e "${BLUE}    sudo apt install -y $PYTHON_VENV_PKG${NC}"
    echo ""
    echo "After installation, run this script again."
    exit 1
else
    echo -e "${GREEN}✓ $PYTHON_VENV_PKG is installed${NC}"
fi
echo ""

# Check if venv already exists
if [ -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment already exists at ./venv${NC}"
    read -p "Do you want to remove it and create a new one? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo -e "${YELLOW}Removing existing virtual environment...${NC}"
        rm -rf venv
    else
        echo "Keeping existing environment. Activating..."
        source venv/bin/activate
        echo -e "${GREEN}✓ Virtual environment activated${NC}"

        # Upgrade pip in existing env
        echo -e "${YELLOW}Upgrading pip...${NC}"
        pip install --upgrade pip setuptools wheel > /dev/null 2>&1
        echo -e "${GREEN}✓ pip upgraded${NC}"

        # Install/update dependencies
        echo -e "${YELLOW}Installing/updating SWE-bench...${NC}"
        pip install -e . 2>&1 | grep -v "Requirement already satisfied" || true
        echo -e "${GREEN}✓ SWE-bench installed${NC}"

        echo ""
        echo -e "${GREEN}Setup complete!${NC}"
        echo ""
        echo -e "${YELLOW}The virtual environment is now active.${NC}"
        echo -e "To use it in a new terminal, run: ${GREEN}source venv/bin/activate${NC}"
        exit 0
    fi
fi

# Create virtual environment
echo -e "${YELLOW}Creating virtual environment...${NC}"
$PYTHON_CMD -m venv venv
echo -e "${GREEN}✓ Virtual environment created at ./venv${NC}"
echo ""

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Upgrade pip
echo -e "${YELLOW}Upgrading pip, setuptools, and wheel...${NC}"
pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo -e "${GREEN}✓ Build tools upgraded${NC}"
echo ""

# Install SWE-bench
echo -e "${YELLOW}Installing SWE-bench with all dependencies...${NC}"
echo "This may take a few minutes..."
pip install -e . 2>&1 | grep -v "Requirement already satisfied" || true
echo -e "${GREEN}✓ SWE-bench installed${NC}"
echo ""

# Verify installation
echo -e "${YELLOW}Verifying installation...${NC}"

# Test basic imports
if python -c "import swebench" 2>/dev/null; then
    echo -e "${GREEN}✓ swebench import successful${NC}"
else
    echo -e "${RED}✗ swebench import failed${NC}"
    exit 1
fi

if python -c "from bs4 import BeautifulSoup" 2>/dev/null; then
    echo -e "${GREEN}✓ beautifulsoup4 import successful${NC}"
else
    echo -e "${RED}✗ beautifulsoup4 import failed${NC}"
    exit 1
fi

if python -c "import docker" 2>/dev/null; then
    echo -e "${GREEN}✓ docker import successful${NC}"
else
    echo -e "${RED}✗ docker import failed${NC}"
    exit 1
fi

if python -c "from swebench.agents import run_agent_workflow" 2>/dev/null; then
    echo -e "${GREEN}✓ agent system import successful${NC}"
else
    echo -e "${RED}✗ agent system import failed${NC}"
    exit 1
fi

# Check Docker connection (optional)
echo ""
echo -e "${YELLOW}Checking Docker connection...${NC}"
if python -c "import docker; docker.from_env().ping()" 2>/dev/null; then
    echo -e "${GREEN}✓ Docker daemon is running${NC}"
else
    echo -e "${YELLOW}⚠ Docker daemon not accessible${NC}"
    echo "  This is optional for agent development but required for validation"
    echo "  Make sure Docker is installed and running"
fi

# Print summary
echo ""
echo -e "${GREEN}================================${NC}"
echo -e "${GREEN}Setup Complete!${NC}"
echo -e "${GREEN}================================${NC}"
echo ""
echo "Virtual environment created at: ./venv"
echo "Python version: $($PYTHON_CMD --version)"
echo ""
echo -e "${YELLOW}The virtual environment is now active in this terminal.${NC}"
echo ""
echo -e "${YELLOW}To activate in a new terminal:${NC}"
echo -e "   ${GREEN}source venv/bin/activate${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo ""
echo "1. Test the agent system:"
echo -e "   ${GREEN}python -m swebench.agents.cli --help${NC}"
echo ""
echo "2. Run an example:"
echo -e "   ${GREEN}python examples/run_agent_example.py${NC}"
echo ""
echo "3. Read the documentation:"
echo -e "   ${GREEN}cat swebench/agents/README.md${NC}"
echo ""
echo -e "To deactivate the environment later, run: ${GREEN}deactivate${NC}"
echo ""
