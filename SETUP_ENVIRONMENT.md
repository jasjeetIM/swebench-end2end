# SWE-bench Environment Setup Guide

This guide will help you create a proper Python virtual environment with all required dependencies for the SWE-bench Agent System.

## Prerequisites

- **Python 3.10+** (Python 3.12 available on this system)
- **Docker** (required for building and testing images)
- **Git** (for cloning repositories)

## Quick Setup (Recommended)

```bash
# 1. Navigate to the project directory
cd /home/jay/swebench-end2end

# 2. Create a virtual environment
python3.12 -m venv venv

# 3. Activate the virtual environment
source venv/bin/activate

# 4. Upgrade pip
pip install --upgrade pip

# 5. Install SWE-bench with all dependencies
pip install -e .

# 6. Verify installation
python -c "import swebench; print(f'SWE-bench version: {swebench.__version__}')"
```

## Step-by-Step Detailed Instructions

### Step 1: Create Virtual Environment

```bash
# Option A: Using venv (recommended)
python3.12 -m venv venv

# Option B: Using virtualenv (if installed)
virtualenv -p python3.12 venv

# Option C: Using conda (if you prefer conda)
conda create -n swebench python=3.12
```

### Step 2: Activate Virtual Environment

```bash
# For venv/virtualenv
source venv/bin/activate

# For conda
conda activate swebench

# You should see (venv) or (swebench) in your prompt
```

### Step 3: Install Dependencies

```bash
# Upgrade pip first
pip install --upgrade pip setuptools wheel

# Install SWE-bench in editable mode with all core dependencies
pip install -e .

# This installs:
# - beautifulsoup4 (for web scraping)
# - chardet (for character encoding detection)
# - datasets (for dataset handling)
# - docker (for Docker operations)
# - ghapi (for GitHub API)
# - GitPython (for Git operations)
# - modal (for cloud execution)
# - pre-commit (for code quality)
# - python-dotenv (for environment variables)
# - requests (for HTTP requests)
# - rich (for terminal output)
# - tenacity (for retries)
# - tqdm (for progress bars)
# - unidiff (for patch handling)
```

### Step 4: Install Optional Dependencies (If Needed)

```bash
# For dataset creation (optional)
pip install -e ".[datasets]"

# For inference/LLM usage (optional)
pip install -e ".[inference]"

# For running tests (optional)
pip install -e ".[test]"

# For documentation (optional)
pip install -e ".[docs]"

# Install everything (all optional dependencies)
pip install -e ".[datasets,inference,test,docs]"
```

## Verify Installation

```bash
# Check Python version
python --version
# Should show: Python 3.12.x

# Check installed packages
pip list | grep -E "swebench|beautifulsoup|docker"

# Test import
python -c "import swebench; from bs4 import BeautifulSoup; import docker; print('✓ All core imports work')"

# Test Docker connection
python -c "import docker; client = docker.from_env(); print(f'✓ Docker connected: {client.version()}')"

# Test agent system
python -c "from swebench.agents import run_agent_workflow; print('✓ Agent system ready')"
```

## Running the Agent System

### Method 1: Using CLI

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run the agent
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0 \
  --verbose
```

### Method 2: Using Example Script

```bash
# Make sure virtual environment is activated
source venv/bin/activate

# Run example
python examples/run_agent_example.py
```

### Method 3: Using Python API

```python
# Make sure virtual environment is activated
source venv/bin/activate

# Start Python REPL
python

# In Python:
from swebench.agents import run_agent_workflow

state = run_agent_workflow(
    repo_url="https://github.com/axios/axios",
    repo_name="axios/axios",
    version="1.6.0",
)

print(f"Success: {state['validation_success']}")
```

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'bs4'"

**Solution**: Install beautifulsoup4
```bash
pip install beautifulsoup4
# or
pip install -e .
```

### Issue: "ModuleNotFoundError: No module named 'docker'"

**Solution**: Install docker
```bash
pip install docker
```

### Issue: "Docker daemon is not running"

**Solution**: Start Docker
```bash
# On Ubuntu/Debian
sudo systemctl start docker

# On macOS
open -a Docker

# Verify
docker ps
```

### Issue: Permission denied for Docker

**Solution**: Add your user to docker group
```bash
sudo usermod -aG docker $USER
# Log out and log back in for changes to take effect
```

### Issue: "Python command not found"

**Solution**: Use python3 or python3.12 explicitly
```bash
python3.12 -m venv venv
```

### Issue: Virtual environment not activating

**Solution**: Check activation command
```bash
# Bash/Zsh
source venv/bin/activate

# Fish
source venv/bin/activate.fish

# Windows (if applicable)
venv\Scripts\activate.bat
```

## Environment Variables (Optional)

Create a `.env` file for configuration:

```bash
# Create .env file
cat > .env << 'EOF'
# GitHub token for private repos (optional)
GITHUB_TOKEN=your_github_token_here

# Docker settings
DOCKER_HOST=unix:///var/run/docker.sock

# Agent cache directory
AGENT_CACHE_DIR=/tmp/swebench-agent-repos

# Logging level
LOG_LEVEL=INFO
EOF
```

## Dependency Tree

Here's what gets installed with `pip install -e .`:

```
swebench/
├── beautifulsoup4 (bs4)     # HTML/XML parsing
├── chardet                  # Character encoding detection
├── datasets                 # HuggingFace datasets
├── docker                   # Docker Python SDK
├── ghapi                    # GitHub API wrapper
├── GitPython               # Git operations
├── modal                   # Cloud execution
├── pre-commit              # Git hooks
├── python-dotenv           # Environment variables
├── requests                # HTTP library
├── rich                    # Terminal formatting
├── tenacity                # Retry logic
├── tqdm                    # Progress bars
└── unidiff                 # Patch parsing
```

## Complete Setup Script

Save this as `setup_env.sh`:

```bash
#!/bin/bash
set -e

echo "Setting up SWE-bench environment..."

# Check Python version
if ! command -v python3.12 &> /dev/null; then
    echo "Error: Python 3.12 not found"
    exit 1
fi

# Create virtual environment
echo "Creating virtual environment..."
python3.12 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install SWE-bench
echo "Installing SWE-bench..."
pip install -e .

# Verify installation
echo "Verifying installation..."
python -c "import swebench; from bs4 import BeautifulSoup; import docker; print('✓ Installation successful')"

echo ""
echo "Setup complete! Activate the environment with:"
echo "  source venv/bin/activate"
echo ""
echo "Then run the agent with:"
echo "  python -m swebench.agents.cli --help"
```

Make it executable and run:

```bash
chmod +x setup_env.sh
./setup_env.sh
```

## Quick Reference

```bash
# Activate environment
source venv/bin/activate

# Deactivate environment
deactivate

# Update dependencies
pip install --upgrade -e .

# Show installed packages
pip list

# Show package info
pip show swebench

# Freeze dependencies
pip freeze > requirements-freeze.txt

# Clean install (if needed)
rm -rf venv
python3.12 -m venv venv
source venv/bin/activate
pip install -e .
```

## Next Steps

After setting up the environment:

1. **Test the agent system**:
   ```bash
   python -m swebench.agents.cli \
     --repo-url https://github.com/axios/axios \
     --repo-name axios/axios \
     --version 1.6.0
   ```

2. **Read the agent documentation**:
   ```bash
   cat swebench/agents/README.md
   ```

3. **Run examples**:
   ```bash
   python examples/run_agent_example.py
   ```

4. **Check logs**:
   ```bash
   tail -f logs/agent/agent.log
   ```

## Additional Resources

- **SWE-bench Docs**: [docs/](docs/)
- **Agent System README**: [swebench/agents/README.md](swebench/agents/README.md)
- **Implementation Guide**: [AGENT_IMPLEMENTATION.md](AGENT_IMPLEMENTATION.md)
- **PyPI Package**: https://pypi.org/project/swebench/

## System Requirements

- **Python**: 3.10, 3.11, or 3.12
- **Docker**: 20.10+ (for building images)
- **Git**: 2.0+ (for cloning repos)
- **Disk Space**: ~10GB for Docker images and repos
- **RAM**: 8GB+ recommended for Docker builds
- **OS**: Linux (tested), macOS (should work), Windows (WSL2)
