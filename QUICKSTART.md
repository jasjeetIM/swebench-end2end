# 🚀 Quick Start Guide - SWE-bench Agent System

Get the SWE-bench agent system up and running in 5 minutes!

## 📋 Prerequisites

- **Python 3.10+** (Python 3.12 recommended)
- **Docker** (for image building and validation)
- **Git** (for cloning repositories)
- **8GB+ RAM** (for Docker builds)

## ⚡ Super Quick Setup (3 Commands)

```bash
# 1. Run the automated setup script
./setup_env.sh

# 2. Activate the virtual environment
source venv/bin/activate

# 3. Test the agent system
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0
```

That's it! 🎉

## 📝 Detailed Setup

### Option 1: Automated Setup (Recommended)

```bash
# Make the setup script executable (if not already)
chmod +x setup_env.sh

# Run the setup script
./setup_env.sh

# The script will:
# ✓ Check Python version (3.10+)
# ✓ Create virtual environment (./venv)
# ✓ Install all dependencies
# ✓ Verify installation
# ✓ Check Docker connection
```

### Option 2: Manual Setup

```bash
# 1. Create virtual environment
python3.12 -m venv venv

# 2. Activate virtual environment
source venv/bin/activate

# 3. Upgrade pip
pip install --upgrade pip

# 4. Install SWE-bench
pip install -e .

# 5. Verify installation
python -c "from swebench.agents import run_agent_workflow; print('✓ Ready!')"
```

## 🎯 Usage Examples

### Example 1: Simple Repository (axios)

```bash
# Activate environment
source venv/bin/activate

# Run agent
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0 \
  --verbose
```

**Expected output:**
```
=====================================
STEP 1/3: Repository Analysis
=====================================
✓ Repository analysis completed

=====================================
STEP 2/3: Configuration Generation
=====================================
✓ Configuration generation completed

=====================================
STEP 3/3: Docker Validation
=====================================
Iteration 1/5: Testing configuration...
✓ Validation succeeded on iteration 1!

STATUS: ✓ SUCCESS
Configuration saved to: swebench/harness/constants/typescript.py
```

### Example 2: Using Python API

```python
# Start Python REPL
python

# Import and run
from swebench.agents import run_agent_workflow

state = run_agent_workflow(
    repo_url="https://github.com/axios/axios",
    repo_name="axios/axios",
    version="1.6.0",
)

# Check result
print(f"Success: {state['validation_success']}")
print(f"Iterations: {state['iteration_count']}/{state['max_iterations']}")

# View configuration
print(state['config_model'])
```

### Example 3: Run Example Script

```bash
# The example script tests multiple repositories
python examples/run_agent_example.py

# Tests:
# 1. axios/axios (simple)
# 2. immutable-js/immutable-js (with commit)
# 3. vuejs/core (complex framework)
```

## 📂 File Structure After Setup

```
swebench-end2end/
├── venv/                           # Virtual environment (created by setup)
├── swebench/
│   └── agents/                     # Agent system code
│       ├── cli.py                  # CLI entry point
│       ├── orchestrator.py         # Workflow orchestration
│       ├── repo_analyzer.py        # Repo analysis
│       ├── config_generator.py     # Config generation
│       ├── docker_validator.py     # Docker validation
│       ├── models/                 # Data models
│       └── utils/                  # Utilities
├── examples/
│   └── run_agent_example.py        # Example usage
├── logs/
│   └── agent/                      # Agent logs (created on first run)
├── setup_env.sh                    # Setup script
├── SETUP_ENVIRONMENT.md            # Detailed setup guide
├── QUICKSTART.md                   # This file
└── AGENT_IMPLEMENTATION.md         # Implementation details
```

## 🔍 Verifying Installation

```bash
# Activate environment
source venv/bin/activate

# Check Python version
python --version
# Should show: Python 3.12.x (or 3.10+)

# Test imports
python -c "from swebench.agents import run_agent_workflow; print('✓ Agent system ready')"

# Check Docker
python -c "import docker; docker.from_env().ping(); print('✓ Docker connected')"

# View help
python -m swebench.agents.cli --help
```

## 🐛 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'bs4'"

```bash
# Make sure you activated the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -e .
```

### Issue: "Docker daemon is not running"

```bash
# Start Docker
sudo systemctl start docker   # Linux
# or
open -a Docker               # macOS

# Verify
docker ps
```

### Issue: "Permission denied" for Docker

```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER

# Log out and log back in
```

### Issue: Virtual environment not activating

```bash
# Make sure you're in the project directory
cd /home/jay/swebench-end2end

# Activate
source venv/bin/activate

# You should see (venv) in your prompt
```

### Issue: Setup script fails

```bash
# Check Python version
python3.12 --version

# If not found, install Python 3.12
# Ubuntu/Debian:
sudo apt update
sudo apt install python3.12 python3.12-venv

# Then re-run setup
./setup_env.sh
```

## 📚 Next Steps

1. **Read the Agent README**:
   ```bash
   cat swebench/agents/README.md
   ```

2. **Understand the Implementation**:
   ```bash
   cat AGENT_IMPLEMENTATION.md
   ```

3. **Try Different Repositories**:
   ```bash
   python -m swebench.agents.cli \
     --repo-url https://github.com/immutable-js/immutable-js \
     --repo-name immutable-js/immutable-js \
     --version 4.3.0
   ```

4. **Check Generated Configuration**:
   ```bash
   cat swebench/harness/constants/typescript.py
   ```

5. **View Logs**:
   ```bash
   tail -f logs/agent/agent.log
   ```

## 🎓 Learning Resources

- **Agent System README**: [swebench/agents/README.md](swebench/agents/README.md)
- **Implementation Guide**: [AGENT_IMPLEMENTATION.md](AGENT_IMPLEMENTATION.md)
- **Setup Details**: [SETUP_ENVIRONMENT.md](SETUP_ENVIRONMENT.md)
- **SWE-bench Docs**: [docs/](docs/)

## 💡 Tips

1. **Use verbose mode** for debugging:
   ```bash
   python -m swebench.agents.cli --verbose ...
   ```

2. **Increase max iterations** for complex repos:
   ```bash
   python -m swebench.agents.cli --max-iterations 10 ...
   ```

3. **Check logs** if something fails:
   ```bash
   ls -lh logs/agent/
   tail -100 logs/agent/agent.log
   ```

4. **Deactivate environment** when done:
   ```bash
   deactivate
   ```

5. **Update dependencies** periodically:
   ```bash
   source venv/bin/activate
   pip install --upgrade -e .
   ```

## 🚦 Status Indicators

When running the agent:

- **✓ SUCCESS** - Configuration validated and saved
- **✗ FAILED** - Validation failed after max iterations
- **✗ ERROR** - Fatal error occurred (check logs)

## 🎯 Common Use Cases

### Use Case 1: Test a New TypeScript Repo

```bash
python -m swebench.agents.cli \
  --repo-url https://github.com/YOUR_ORG/YOUR_REPO \
  --repo-name YOUR_ORG/YOUR_REPO \
  --version 1.0.0
```

### Use Case 2: Test with Specific Commit

```bash
python -m swebench.agents.cli \
  --repo-url https://github.com/vuejs/core \
  --repo-name vuejs/core \
  --version 3.4.0 \
  --base-commit abc123def456
```

### Use Case 3: Debug Failed Configuration

```bash
# Run with verbose logging
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0 \
  --max-iterations 10 \
  --verbose

# Check logs
tail -f logs/agent/agent.log

# Check validation logs
ls logs/run_evaluation/agent-validation/
```

## 📞 Getting Help

- **Check logs**: `logs/agent/agent.log`
- **Read documentation**: `swebench/agents/README.md`
- **Run with --verbose**: Get detailed output
- **Check examples**: `examples/run_agent_example.py`

## 🎉 You're All Set!

You now have a fully functional SWE-bench agent system. Start automating Docker configurations for TypeScript/JavaScript repositories!

```bash
# Quick test
source venv/bin/activate
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0
```

Happy automating! 🚀
