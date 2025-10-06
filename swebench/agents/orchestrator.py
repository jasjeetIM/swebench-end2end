"""
Orchestrator - LangGraph-based workflow for agent coordination.

NOTE: This implementation uses a simplified sequential workflow without LangGraph
as a dependency. In production, you would use LangGraph for more sophisticated
orchestration with conditional edges, retry logic, and parallel execution.

To use LangGraph in the future:
    from langgraph.graph import StateGraph, END
"""

from typing import Optional
from pathlib import Path
import logging

from .models.state_model import AgentState, create_initial_state
from .repo_analyzer import RepoAnalyzerAgent
from .config_generator import ConfigGeneratorAgent
from .docker_validator import DockerValidatorAgent

logger = logging.getLogger(__name__)


class AgentOrchestrator:
    """
    Orchestrates the agent workflow for automated Docker configuration.

    Sequential workflow:
    1. Repo Analyzer Agent - Analyze repository
    2. Config Generator Agent - Generate configuration
    3. Docker Validator Agent - Validate and fix iteratively
    """

    def __init__(
        self,
        cache_dir: Optional[Path] = None,
        max_validation_iterations: int = 5,
    ):
        """
        Initialize the orchestrator.

        Args:
            cache_dir: Directory to cache cloned repos
            max_validation_iterations: Max iterations for Docker validation
        """
        self.repo_analyzer = RepoAnalyzerAgent(cache_dir=cache_dir)
        self.config_generator = ConfigGeneratorAgent()
        self.docker_validator = DockerValidatorAgent(
            max_iterations=max_validation_iterations
        )
        logger.info("AgentOrchestrator initialized")

    def run_workflow(
        self,
        repo_url: str,
        repo_name: str,
        language: str = "typescript",
        version: str = "latest",
        base_commit: Optional[str] = None,
        max_iterations: int = 5,
    ) -> AgentState:
        """
        Run the complete agent workflow.

        Args:
            repo_url: GitHub repository URL
            repo_name: Repository name (owner/repo)
            language: Programming language (default: "typescript")
            version: Version string for config (default: "latest")
            base_commit: Git commit SHA (optional)
            max_iterations: Max validation iterations (default: 5)

        Returns:
            Final AgentState with results
        """
        # Create initial state
        state = create_initial_state(
            repo_url=repo_url,
            repo_name=repo_name,
            language=language,
            version=version,
            base_commit=base_commit,
            max_iterations=max_iterations,
        )

        logger.info(f"Starting workflow for: {repo_name}")
        logger.info(f"Workflow ID: {state['workflow_id']}")

        # Step 1: Analyze Repository
        logger.info("\n" + "=" * 70)
        logger.info("STEP 1/3: Repository Analysis")
        logger.info("=" * 70)

        state = self.repo_analyzer.analyze(state)

        if state.get("error_occurred"):
            logger.error(f"Repository analysis failed: {state['error_message']}")
            return state

        logger.info("✓ Repository analysis completed")

        # Step 2: Generate Configuration
        logger.info("\n" + "=" * 70)
        logger.info("STEP 2/3: Configuration Generation")
        logger.info("=" * 70)

        state = self.config_generator.generate(state)

        if state.get("error_occurred"):
            logger.error(f"Configuration generation failed: {state['error_message']}")
            return state

        logger.info("✓ Configuration generation completed")

        # Step 3: Validate Docker Configuration
        logger.info("\n" + "=" * 70)
        logger.info("STEP 3/3: Docker Validation")
        logger.info("=" * 70)

        state = self.docker_validator.validate(state)

        if state.get("error_occurred"):
            logger.error(f"Docker validation failed: {state['error_message']}")
            return state

        # Final status
        logger.info("\n" + "=" * 70)
        logger.info("WORKFLOW COMPLETE")
        logger.info("=" * 70)

        if state["validation_success"]:
            logger.info("✓ SUCCESS: Docker configuration validated")
            logger.info(f"  Iterations: {state['iteration_count']}/{max_iterations}")
            logger.info(f"  Test instance: {state.get('test_instance_id')}")
        else:
            logger.warning("✗ FAILED: Docker validation failed")
            logger.info(f"  Iterations: {state['iteration_count']}/{max_iterations}")

        return state


def run_agent_workflow(
    repo_url: str,
    repo_name: str,
    language: str = "typescript",
    version: str = "latest",
    base_commit: Optional[str] = None,
    max_iterations: int = 5,
    cache_dir: Optional[Path] = None,
) -> AgentState:
    """
    Convenience function to run the agent workflow.

    Args:
        repo_url: GitHub repository URL
        repo_name: Repository name (owner/repo)
        language: Programming language (default: "typescript")
        version: Version string (default: "latest")
        base_commit: Git commit SHA (optional)
        max_iterations: Max validation iterations (default: 5)
        cache_dir: Directory to cache repos (optional)

    Returns:
        Final AgentState
    """
    orchestrator = AgentOrchestrator(
        cache_dir=cache_dir, max_validation_iterations=max_iterations
    )

    return orchestrator.run_workflow(
        repo_url=repo_url,
        repo_name=repo_name,
        language=language,
        version=version,
        base_commit=base_commit,
        max_iterations=max_iterations,
    )


# Future: LangGraph implementation example
"""
from langgraph.graph import StateGraph, END

def create_langgraph_workflow(orchestrator: AgentOrchestrator) -> StateGraph:
    '''
    Create a LangGraph workflow with conditional edges and retry logic.
    '''
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("analyze_repo", orchestrator.repo_analyzer.analyze)
    workflow.add_node("generate_config", orchestrator.config_generator.generate)
    workflow.add_node("validate_docker", orchestrator.docker_validator.validate)

    # Add edges
    workflow.add_edge("analyze_repo", "generate_config")
    workflow.add_edge("generate_config", "validate_docker")

    # Conditional edge for retry logic
    def should_retry(state: AgentState) -> str:
        if state.get("error_occurred"):
            return "error"
        if state.get("validation_success"):
            return "done"
        if state["iteration_count"] < state["max_iterations"]:
            return "retry"
        return "done"

    workflow.add_conditional_edges(
        "validate_docker",
        should_retry,
        {
            "retry": "generate_config",  # Feedback loop
            "done": END,
            "error": END,
        }
    )

    workflow.set_entry_point("analyze_repo")

    return workflow.compile()
"""
