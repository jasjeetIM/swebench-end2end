# Manual Installation Guide - SWE-bench Agent System

## 🔧 Step-by-Step Manual Setup

Follow these steps if the automated script doesn't work or you prefer manual installation.

## Step 1: Install System Dependencies

```bash
# Update package list
sudo apt update

# Install Python 3.12 and venv package
sudo apt install -y python3.12 python3.12-venv

# Verify installation
python3.12 --version
# Should show: Python 3.12.x
```

## Step 2: Create Virtual Environment

```bash
# Navigate to project directory
cd /home/jay/swebench-end2end

# Create virtual environment
python3.12 -m venv venv

# You should see a new 'venv' directory
ls -la venv/
```

## Step 3: Activate Virtual Environment

```bash
# Activate the environment
source venv/bin/activate

# Your prompt should change to show (venv)
# Example: (venv) jay@hostname:~/swebench-end2end$
```

## Step 4: Upgrade pip

```bash
# Upgrade pip to latest version
pip install --upgrade pip setuptools wheel

# Verify pip version
pip --version
# Should show: pip 24.x or higher
```

## Step 5: Install SWE-bench

```bash
# Install in editable mode with all dependencies
pip install -e .

# This will install:
# - beautifulsoup4
# - docker
# - datasets
# - GitPython
# - requests
# - tqdm
# - and other dependencies from pyproject.toml
```

## Step 6: Verify Installation

```bash
# Test Python imports
python -c "import swebench; print('✓ swebench works')"
python -c "from bs4 import BeautifulSoup; print('✓ beautifulsoup4 works')"
python -c "import docker; print('✓ docker works')"
python -c "from swebench.agents import run_agent_workflow; print('✓ agents work')"

# Check Docker connection
python -c "import docker; docker.from_env().ping(); print('✓ Docker connected')"
```

## Step 7: Test the Agent System

```bash
# Run help
python -m swebench.agents.cli --help

# Test with a simple repository
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0
```

## 🐛 Troubleshooting

### Issue: "ensurepip is not available"

**Solution:**
```bash
sudo apt update
sudo apt install -y python3.12-venv
```

### Issue: "pip: command not found"

**Solution:**
```bash
# Make sure virtual environment is activated
source venv/bin/activate

# If still not working, install pip manually
python -m ensurepip --upgrade
```

### Issue: "Permission denied" errors

**Solution:**
```bash
# Don't use sudo with pip inside virtual environment
# Instead, make sure you're in the venv:
source venv/bin/activate

# Then install without sudo
pip install -e .
```

### Issue: Docker connection fails

**Solution:**
```bash
# Check Docker is installed
docker --version

# Check Docker is running
sudo systemctl status docker

# Start Docker if needed
sudo systemctl start docker

# Add your user to docker group (to avoid sudo)
sudo usermod -aG docker $USER
# Then log out and log back in
```

### Issue: Module import errors after installation

**Solution:**
```bash
# Clean install
deactivate  # Exit current venv
rm -rf venv  # Remove old venv
python3.12 -m venv venv  # Create fresh venv
source venv/bin/activate  # Activate
pip install --upgrade pip  # Upgrade pip
pip install -e .  # Install dependencies
```

## 📋 Installation Checklist

- [ ] Python 3.12 installed (`python3.12 --version`)
- [ ] python3.12-venv installed (`dpkg -l | grep python3.12-venv`)
- [ ] Virtual environment created (`ls venv/`)
- [ ] Virtual environment activated (`echo $VIRTUAL_ENV`)
- [ ] pip upgraded (`pip --version`)
- [ ] SWE-bench installed (`pip show swebench`)
- [ ] beautifulsoup4 installed (`python -c "import bs4"`)
- [ ] docker installed (`python -c "import docker"`)
- [ ] Agent system works (`python -c "from swebench.agents import run_agent_workflow"`)
- [ ] Docker running (`docker ps`)

## 🎯 Quick Commands Reference

```bash
# Create virtual environment
python3.12 -m venv venv

# Activate
source venv/bin/activate

# Deactivate
deactivate

# Install dependencies
pip install -e .

# Test agent
python -m swebench.agents.cli --help

# View installed packages
pip list

# Update dependencies
pip install --upgrade -e .

# Clean reinstall
rm -rf venv && python3.12 -m venv venv && source venv/bin/activate && pip install -e .
```

## 🔄 Daily Usage

### Starting Work

```bash
# 1. Navigate to project
cd /home/jay/swebench-end2end

# 2. Activate environment
source venv/bin/activate

# 3. Update dependencies (optional, weekly)
pip install --upgrade -e .
```

### Ending Work

```bash
# Deactivate environment
deactivate
```

## 📦 What Gets Installed

From [pyproject.toml](pyproject.toml):

**Core dependencies:**
- beautifulsoup4 - HTML/XML parsing
- chardet - Character encoding
- datasets - HuggingFace datasets
- docker - Docker Python SDK
- ghapi - GitHub API
- GitPython - Git operations
- modal - Cloud execution
- pre-commit - Git hooks
- python-dotenv - Environment variables
- requests - HTTP requests
- rich - Terminal formatting
- tenacity - Retry logic
- tqdm - Progress bars
- unidiff - Patch parsing

## 🚀 Next Steps

After successful installation:

1. Read the Quick Start:
   ```bash
   cat QUICKSTART.md
   ```

2. Read the Agent README:
   ```bash
   cat swebench/agents/README.md
   ```

3. Run examples:
   ```bash
   python examples/run_agent_example.py
   ```

4. Test with your own repository:
   ```bash
   python -m swebench.agents.cli \
     --repo-url https://github.com/YOUR_ORG/YOUR_REPO \
     --repo-name YOUR_ORG/YOUR_REPO \
     --version 1.0.0
   ```

## ✅ Success Indicators

You know it's working when:

1. Virtual environment activates without errors
2. All Python imports succeed
3. Docker connection works
4. Agent CLI shows help text
5. Example script runs successfully

Good luck! 🎉
