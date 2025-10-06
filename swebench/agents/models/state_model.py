"""
State Model - Shared state for LangGraph workflow.
"""

from typing import TypedDict, Optional, Dict, List, Any
from .repo_model import RepoModel
from .config_model import ConfigModel


class AgentState(TypedDict, total=False):
    """
    Shared state for the agent workflow.

    This state is passed between agents in the LangGraph workflow.
    Each agent reads from and writes to this state.
    """

    # Input parameters
    repo_url: str
    repo_name: str  # Format: "owner/repo"
    language: str  # "typescript" for MVP
    base_commit: Optional[str]  # Git commit SHA
    version: str  # Version string for the config

    # Repo analysis results
    repo_model: Optional[Dict[str, Any]]  # RepoModel.to_dict()
    repo_analysis_complete: bool

    # Config generation results
    config_model: Optional[Dict[str, Any]]  # ConfigModel.to_dict()
    config_generation_complete: bool

    # Docker validation results
    validation_complete: bool
    validation_success: bool
    validation_logs: List[str]
    iteration_count: int
    max_iterations: int

    # Error tracking
    error_occurred: bool
    error_message: str
    error_stage: str  # "analyze", "generate", "validate"

    # Final outputs
    final_config_path: Optional[str]
    test_instance_id: Optional[str]

    # Metadata
    workflow_id: str
    timestamp: str


def create_initial_state(
    repo_url: str,
    repo_name: str,
    language: str = "typescript",
    version: str = "latest",
    base_commit: Optional[str] = None,
    max_iterations: int = 5,
) -> AgentState:
    """
    Create initial state for the agent workflow.

    Args:
        repo_url: GitHub repository URL
        repo_name: Repository name in format "owner/repo"
        language: Programming language (default: "typescript")
        version: Version string for config (default: "latest")
        base_commit: Git commit SHA (optional)
        max_iterations: Max validation iterations (default: 5)

    Returns:
        Initial AgentState
    """
    import uuid
    from datetime import datetime

    return AgentState(
        repo_url=repo_url,
        repo_name=repo_name,
        language=language,
        base_commit=base_commit,
        version=version,
        repo_model=None,
        repo_analysis_complete=False,
        config_model=None,
        config_generation_complete=False,
        validation_complete=False,
        validation_success=False,
        validation_logs=[],
        iteration_count=0,
        max_iterations=max_iterations,
        error_occurred=False,
        error_message="",
        error_stage="",
        final_config_path=None,
        test_instance_id=None,
        workflow_id=str(uuid.uuid4())[:8],
        timestamp=datetime.now().isoformat(),
    )
