# SWE-bench Agent System

**Automated Docker Configuration for TypeScript/JavaScript Repositories**

This agent system automates the creation of Docker configurations for SWE-bench evaluation, eliminating manual configuration work.

## 🎯 Overview

The agent system consists of three specialized agents orchestrated in a sequential workflow:

1. **Repo Analyzer Agent** - Analyzes GitHub repositories and extracts metadata
2. **Config Generator Agent** - Generates SWE-bench Docker configurations
3. **Docker Validator Agent** - Validates configurations with iterative error recovery

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Agent Orchestrator                        │
│              (Sequential Workflow Pattern)                   │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌──────────────┐   ┌──────────────────┐
│   Repo       │   │  Config      │   │   Docker         │
│   Analyzer   │──▶│  Generator   │──▶│   Validator      │
│   Agent      │   │  Agent       │   │   Agent          │
└──────────────┘   └──────────────┘   └──────────────────┘
        │                  │                    │
        ▼                  ▼                    ▼
  [Repo Model]      [Config Model]       [Validation Log]
```

### File Structure

```
swebench/agents/
├── __init__.py              # Package exports
├── __main__.py              # Module entry point
├── cli.py                   # Command-line interface
├── orchestrator.py          # Workflow orchestration
├── repo_analyzer.py         # Repository analysis agent
├── config_generator.py      # Configuration generation agent
├── docker_validator.py      # Docker validation agent
├── models/
│   ├── __init__.py
│   ├── repo_model.py        # Repository metadata model
│   ├── config_model.py      # Configuration model
│   └── state_model.py       # Workflow state model
└── utils/
    ├── __init__.py
    ├── github_utils.py      # GitHub repo fetching
    ├── package_parsers.py   # package.json, tsconfig.json parsers
    ├── dependency_mapper.py # npm → system package mapping
    └── error_analyzer.py    # Docker error analysis
```

## 🚀 Quick Start

### Installation

Ensure you have SWE-bench installed with Docker support:

```bash
pip install -e .
```

### Basic Usage

```bash
python -m swebench.agents.cli \
  --repo-url https://github.com/axios/axios \
  --repo-name axios/axios \
  --version 1.6.0
```

### With Specific Commit

```bash
python -m swebench.agents.cli \
  --repo-url https://github.com/vuejs/core \
  --repo-name vuejs/core \
  --version 3.4.0 \
  --base-commit abc123def456789
```

### With Custom Settings

```bash
python -m swebench.agents.cli \
  --repo-url https://github.com/microsoft/TypeScript \
  --repo-name microsoft/TypeScript \
  --version 5.3.0 \
  --max-iterations 10 \
  --verbose
```

## 📖 How It Works

### Step 1: Repository Analysis

The **Repo Analyzer Agent**:
- Clones the GitHub repository
- Parses `package.json`, `tsconfig.json`, lock files
- Detects package manager (npm, yarn, pnpm)
- Identifies Node.js version requirements
- Extracts dependencies and infers system packages
- Detects test framework

**Output**: `RepoModel` with repository metadata

### Step 2: Configuration Generation

The **Config Generator Agent**:
- Takes the `RepoModel` as input
- Generates install commands based on package manager
- Creates Docker specifications (Node version, variants)
- Maps npm dependencies to system packages (apt)
- Generates test and build commands
- Writes configuration to `harness/constants/typescript.py`

**Output**: `ConfigModel` with SWE-bench configuration

### Step 3: Docker Validation

The **Docker Validator Agent**:
- Creates a test SWE-bench instance
- Builds Docker images using existing SWE-bench infrastructure
- Runs the test instance to validate setup
- Analyzes failure logs if validation fails
- Proposes and applies fixes automatically
- Iterates until success or max iterations reached

**Output**: Validated configuration with iteration logs

## 🔧 Configuration Models

### RepoModel

```python
@dataclass
class RepoModel:
    repo: str                    # "owner/repo"
    language: str                # "typescript"
    base_commit: str             # Git commit SHA
    package_manager: str         # "npm" | "yarn" | "pnpm"
    node_version: str            # "20"
    install_command: List[str]   # ["npm install"]
    test_command: str            # "npm test"
    build_command: Optional[str] # "npm run build"
    dependencies: Dict           # Production deps
    dev_dependencies: Dict       # Dev deps
    test_framework: str          # "jest" | "vitest" | ...
    system_deps: List[str]       # ["chromium", "libcairo2-dev"]
    has_typescript: bool         # True
    has_build_step: bool         # True
```

### ConfigModel

```python
@dataclass
class ConfigModel:
    repo: str                    # "owner/repo"
    version: str                 # "5.3.0"
    install: List[str]           # ["npm install"]
    test_cmd: str                # "npm test"
    build: Optional[List[str]]   # ["npm run build"]
    docker_specs: Dict           # {"node_version": "20", "_variant": "js_2"}
    apt_pkgs: List[str]          # ["chromium", "build-essential"]
    env_vars: Dict               # Environment variables
```

## 🐛 Error Recovery

The Docker Validator Agent includes automatic error recovery:

### Pattern-Based Error Detection

- **Missing package**: `E: Unable to locate package X` → Remove invalid package
- **Node not found**: Node.js installation failed → Fallback to Node 18
- **npm ERR!**: npm install errors → Add `--legacy-peer-deps` flag
- **Chromium missing**: Browser tests fail → Add `chromium` package
- **gyp ERR!**: Native module compilation → Add `build-essential`

### Iterative Fix Loop

```
1. Write config → 2. Build images → 3. Run tests
                         ↓ failure
                    4. Analyze logs
                         ↓
                    5. Propose fix
                         ↓
                    6. Apply fix → (back to 1)
```

Maximum iterations: 5 (configurable)

## 📊 Output

### Success

```
WORKFLOW SUMMARY
================

Repository: axios/axios
Workflow ID: a7b3c2d1

--- Repository Analysis ---
✓ Complete
  Language: typescript
  Package Manager: npm
  Node Version: 18
  Test Framework: jest
  System Deps: 2 packages

--- Configuration Generation ---
✓ Complete
  Version: 1.6.0
  Install Commands: 1
  Test Command: npm test
  APT Packages: 2

--- Docker Validation ---
✓ Success
  Iterations: 2/5
  Test Instance: axios__axios-agent-test-1.6.0

STATUS: ✓ SUCCESS
Configuration saved to: swebench/harness/constants/typescript.py
```

### Failure Example

```
--- Docker Validation ---
✗ Failed
  Iterations: 5/5
  Validation Logs:
    Iteration 1: install_failure: Missing module: @types/node
    Iteration 2: build_failure_generic: Docker build failed
    Iteration 3: install_failure: gyp ERR!
    Iteration 4: timeout: Test execution timed out
    Iteration 5: Max iterations (5) reached

STATUS: ✗ FAILED
```

## 🧪 Testing

### Test a Single Repo

```bash
python -m swebench.agents.cli \
  --repo-url https://github.com/immutable-js/immutable-js \
  --repo-name immutable-js/immutable-js \
  --version 4.3.0 \
  --verbose
```

### Check Generated Configuration

```bash
cat swebench/harness/constants/typescript.py
```

### Manually Test with SWE-bench

```bash
# Prepare images
python swebench/harness/prepare_images.py \
  --dataset_name path/to/your/dataset.json \
  --instance_ids immutable-js__immutable-js-test-4.3.0

# Run evaluation
python swebench/harness/run_evaluation.py \
  --dataset_name path/to/your/dataset.json \
  --predictions_path path/to/predictions.json \
  --run_id test-run
```

## 🔍 Logging

Logs are written to:
- Console (stdout)
- `logs/agent/agent.log` - Main agent workflow log
- `logs/build_images/` - Docker build logs (per image)
- `logs/run_evaluation/agent-validation/` - Test execution logs

Enable verbose logging with `--verbose` flag.

## 🛠️ Advanced Usage

### Programmatic API

```python
from swebench.agents import run_agent_workflow

state = run_agent_workflow(
    repo_url="https://github.com/vuejs/core",
    repo_name="vuejs/core",
    version="3.4.0",
    max_iterations=10,
)

if state["validation_success"]:
    print(f"Success! Config: {state['config_model']}")
else:
    print(f"Failed: {state['error_message']}")
```

### Custom Cache Directory

```python
from pathlib import Path
from swebench.agents import AgentOrchestrator

orchestrator = AgentOrchestrator(
    cache_dir=Path("/custom/cache/dir"),
    max_validation_iterations=10,
)

state = orchestrator.run_workflow(
    repo_url="https://github.com/axios/axios",
    repo_name="axios/axios",
    version="1.6.0",
)
```

## 📝 Limitations

### Current Limitations

1. **Language Support**: Only TypeScript/JavaScript (MVP)
2. **Package Managers**: npm, yarn, pnpm (common ones)
3. **System Dependencies**: Limited mapping (can be extended)
4. **LLM Integration**: Pattern-based only (no LLM for now)
5. **Monorepos**: Limited support for complex workspaces

### Future Enhancements

- [ ] LLM-based error analysis for complex failures
- [ ] Support for more languages (Python, Go, Rust)
- [ ] Parallel agent execution with LangGraph
- [ ] Learning from past failures
- [ ] Monorepo/workspace detection
- [ ] Interactive mode for human-in-the-loop

## 🤝 Contributing

### Adding New Dependency Mappings

Edit `swebench/agents/utils/dependency_mapper.py`:

```python
PACKAGE_TO_SYSTEM_DEPS = {
    "your-npm-package": ["required-apt-package"],
}
```

### Adding New Error Patterns

Edit `swebench/agents/utils/error_analyzer.py`:

```python
ERROR_PATTERNS = {
    "your_error_type": re.compile(r"your regex pattern"),
}
```

## 📚 References

- [SWE-bench Documentation](../../../docs/)
- [Docker Build Process](../../harness/docker_build.py)
- [Constants Configuration](../../harness/constants/)
- [SWE-agent Paper](https://arxiv.org/abs/2405.15793)
- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)

## 📄 License

Same as SWE-bench parent project.
