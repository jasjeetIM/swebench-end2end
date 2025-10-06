#!/bin/bash

# SWE-bench Agent Setup Verification Script
# Verifies that all prerequisites are correctly configured

set -e

echo "========================================"
echo "SWE-bench Agent Setup Verification"
echo "========================================"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Track if any checks fail
FAILED=0

# Check 1: Python version
echo -n "Checking Python version... "
PYTHON_VERSION=$(python3 --version 2>&1 | grep -oP '\d+\.\d+' | head -1)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -ge 3 ] && [ "$PYTHON_MINOR" -ge 10 ]; then
    echo -e "${GREEN}✓${NC} Python $PYTHON_VERSION (>= 3.10 required)"
else
    echo -e "${RED}✗${NC} Python $PYTHON_VERSION found, but >= 3.10 required"
    FAILED=1
fi

# Check 2: Virtual environment
echo -n "Checking virtual environment... "
if [ -n "$VIRTUAL_ENV" ]; then
    echo -e "${GREEN}✓${NC} Virtual environment active: $VIRTUAL_ENV"
else
    echo -e "${YELLOW}⚠${NC} No virtual environment detected"
    echo "  Recommendation: Run 'source venv/bin/activate'"
fi

# Check 3: Docker installed
echo -n "Checking Docker installation... "
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | grep -oP '\d+\.\d+\.\d+' | head -1)
    echo -e "${GREEN}✓${NC} Docker $DOCKER_VERSION installed"
else
    echo -e "${RED}✗${NC} Docker not found"
    echo "  Install: https://docs.docker.com/engine/install/"
    FAILED=1
fi

# Check 4: Docker group membership
echo -n "Checking Docker group membership... "
if groups | grep -q docker; then
    echo -e "${GREEN}✓${NC} User is in docker group"
else
    echo -e "${RED}✗${NC} User is NOT in docker group"
    echo ""
    echo "  To fix, run:"
    echo "    sudo usermod -aG docker \$USER"
    echo ""
    echo "  Then logout and login again, or run:"
    echo "    newgrp docker"
    echo ""
    FAILED=1
fi

# Check 5: Docker socket access
echo -n "Checking Docker socket permissions... "
if [ -S /var/run/docker.sock ]; then
    if docker ps &> /dev/null; then
        echo -e "${GREEN}✓${NC} Can access Docker socket"
    else
        echo -e "${RED}✗${NC} Cannot access Docker socket"
        echo ""
        echo "  This usually means you need to logout/login after adding to docker group."
        echo "  Quick fix (for current terminal session only):"
        echo "    newgrp docker"
        echo ""
        echo "  Permanent fix:"
        echo "    1. Ensure you're in docker group: sudo usermod -aG docker \$USER"
        echo "    2. Logout and login again"
        echo ""
        FAILED=1
    fi
else
    echo -e "${RED}✗${NC} Docker socket not found at /var/run/docker.sock"
    echo "  Is Docker daemon running? Try: sudo systemctl start docker"
    FAILED=1
fi

# Check 6: Required Python packages
echo -n "Checking Python package installation... "
if python3 -c "import docker, bs4, unidiff" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Required packages installed"
else
    echo -e "${RED}✗${NC} Some packages missing"
    echo "  Run: pip install -e ."
    FAILED=1
fi

# Check 7: SWE-bench package installed
echo -n "Checking swebench package... "
if python3 -c "import swebench" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} swebench package available"
else
    echo -e "${RED}✗${NC} swebench package not found"
    echo "  Run: pip install -e ."
    FAILED=1
fi

# Check 8: Agent modules
echo -n "Checking agent modules... "
if python3 -c "from swebench.agents.cli import main" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} Agent modules available"
else
    echo -e "${RED}✗${NC} Agent modules not found"
    echo "  Ensure swebench/agents/ directory exists"
    FAILED=1
fi

# Summary
echo ""
echo "========================================"
if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}All checks passed!${NC}"
    echo ""
    echo "You can now run the agent:"
    echo "  python -m swebench.agents.cli --repo-url https://github.com/axios/axios --repo-name axios/axios --version 1.6.0"
else
    echo -e "${RED}Some checks failed. Please fix the issues above.${NC}"
    echo ""
    echo "Common fixes:"
    echo "  1. Docker permissions: sudo usermod -aG docker \$USER && newgrp docker"
    echo "  2. Install packages: pip install -e ."
    echo "  3. Activate venv: source venv/bin/activate"
fi
echo "========================================"

exit $FAILED
