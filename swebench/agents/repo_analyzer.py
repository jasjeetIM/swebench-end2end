"""
Repo Analyzer Agent - Analyzes GitHub repositories and extracts metadata.
"""

from pathlib import Path
from typing import Dict, Optional
import logging

from .models.repo_model import RepoModel
from .models.state_model import AgentState
from .utils.github_utils import GitHubRepoFetcher
from .utils.package_parsers import PackageJsonParser, TsConfigParser, LockFileDetector
from .utils.dependency_mapper import DependencyMapper

logger = logging.getLogger(__name__)


class RepoAnalyzerAgent:
    """
    Agent responsible for analyzing repositories and extracting configuration metadata.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the Repo Analyzer Agent.

        Args:
            cache_dir: Directory to cache cloned repos
        """
        self.fetcher = GitHubRepoFetcher(cache_dir=cache_dir)
        logger.info("RepoAnalyzerAgent initialized")

    def analyze(self, state: AgentState) -> AgentState:
        """
        Analyze a repository and update the agent state.

        This is the main entry point called by the LangGraph workflow.

        Args:
            state: Current agent state

        Returns:
            Updated agent state with repo_model populated
        """
        try:
            logger.info(f"Analyzing repository: {state['repo_url']}")

            # Clone the repository
            repo_path = self._clone_repository(state)

            # Parse repository files
            repo_model = self._analyze_repository(repo_path, state)

            # Update state
            state["repo_model"] = repo_model.to_dict()
            state["repo_analysis_complete"] = True

            logger.info(f"Repository analysis complete: {state['repo_name']}")
            return state

        except Exception as e:
            logger.error(f"Error analyzing repository: {e}", exc_info=True)
            state["error_occurred"] = True
            state["error_message"] = str(e)
            state["error_stage"] = "analyze"
            return state

    def _clone_repository(self, state: AgentState) -> Path:
        """Clone the repository to local cache."""
        repo_url = state["repo_url"]
        base_commit = state.get("base_commit")

        logger.info(f"Cloning repository: {repo_url}")
        repo_path = self.fetcher.clone_repo(
            repo_url=repo_url, commit=base_commit, shallow=not base_commit
        )

        logger.info(f"Repository cloned to: {repo_path}")
        return repo_path

    def _analyze_repository(self, repo_path: Path, state: AgentState) -> RepoModel:
        """
        Analyze repository files and extract metadata.

        Args:
            repo_path: Path to cloned repository
            state: Current agent state

        Returns:
            RepoModel with extracted metadata
        """
        # Find package.json
        package_json_path = repo_path / "package.json"
        if not package_json_path.exists():
            raise FileNotFoundError(f"package.json not found in {repo_path}")

        # Parse package.json
        pkg_parser = PackageJsonParser(package_json_path)

        # Detect package manager
        package_manager = self._detect_package_manager(repo_path, pkg_parser)

        # Detect Node.js version
        node_version, node_version_source = self._detect_node_version(repo_path, pkg_parser)

        # Get dependencies
        dependencies = pkg_parser.get_dependencies()
        dev_dependencies = pkg_parser.get_dev_dependencies()

        # Infer test framework
        test_framework = pkg_parser.infer_test_framework()

        # Get commands
        install_command = DependencyMapper.get_install_command(package_manager)
        test_command = pkg_parser.get_test_command()
        build_command = pkg_parser.get_build_command()

        # Detect TypeScript
        has_typescript = pkg_parser.has_typescript()

        # Get system dependencies
        system_deps = self._infer_system_dependencies(
            dependencies, dev_dependencies, test_framework
        )

        # Get base commit
        base_commit = state.get("base_commit") or self._get_current_commit(repo_path)

        # Create RepoModel
        repo_model = RepoModel(
            repo=state["repo_name"],
            language=state["language"],
            base_commit=base_commit,
            package_manager=package_manager,
            lock_file_type=LockFileDetector.detect_lock_file(repo_path),
            node_version=node_version,
            node_version_source=node_version_source,
            install_command=install_command,
            build_command=build_command,
            test_command=test_command,
            dependencies=dependencies,
            dev_dependencies=dev_dependencies,
            test_framework=test_framework,
            system_deps=system_deps,
            has_typescript=has_typescript,
            has_build_step=build_command is not None,
            package_json_path="package.json",
            repo_url=state["repo_url"],
        )

        logger.info(f"Repo Model: {repo_model.to_dict()}")
        return repo_model

    def _detect_package_manager(
        self, repo_path: Path, pkg_parser: PackageJsonParser
    ) -> str:
        """
        Detect package manager from lock files or package.json.

        Priority:
        1. Lock file presence
        2. packageManager field in package.json
        3. Default to npm
        """
        # Check lock files first
        lock_file_pm = LockFileDetector.detect_lock_file(repo_path)
        if lock_file_pm:
            logger.info(f"Detected package manager from lock file: {lock_file_pm}")
            return lock_file_pm

        # Check package.json
        pkg_json_pm = pkg_parser.get_package_manager()
        if pkg_json_pm:
            logger.info(f"Detected package manager from package.json: {pkg_json_pm}")
            return pkg_json_pm

        # Default
        logger.info("No package manager detected, defaulting to npm")
        return "npm"

    def _detect_node_version(
        self, repo_path: Path, pkg_parser: PackageJsonParser
    ) -> tuple[str, str]:
        """
        Detect Node.js version.

        Priority:
        1. .nvmrc file
        2. package.json engines.node
        3. Default to 20
        """
        # Check .nvmrc
        nvmrc_path = repo_path / ".nvmrc"
        if nvmrc_path.exists():
            try:
                version = nvmrc_path.read_text().strip()
                # Extract major version
                if version.startswith("v"):
                    version = version[1:]
                major_version = version.split(".")[0]
                logger.info(f"Node version from .nvmrc: {major_version}")
                return major_version, "nvmrc"
            except Exception as e:
                logger.warning(f"Failed to read .nvmrc: {e}")

        # Check package.json engines
        engines_version = pkg_parser.get_node_version_from_engines()
        if engines_version:
            logger.info(f"Node version from package.json engines: {engines_version}")
            return engines_version, "package.json"

        # Default
        logger.info("Node version not specified, defaulting to 20")
        return "20", "default"

    def _infer_system_dependencies(
        self,
        dependencies: Dict[str, str],
        dev_dependencies: Dict[str, str],
        test_framework: Optional[str],
    ) -> list[str]:
        """
        Infer system dependencies from npm packages.

        Args:
            dependencies: Production dependencies
            dev_dependencies: Development dependencies
            test_framework: Test framework name

        Returns:
            List of system package names
        """
        all_deps = {**dependencies, **dev_dependencies}
        system_deps = DependencyMapper.get_system_deps_from_dependencies(all_deps)

        # Add test framework dependencies
        if test_framework:
            framework_deps = DependencyMapper.infer_test_framework_deps(test_framework)
            system_deps.extend(framework_deps)

        # Remove duplicates and sort
        system_deps = sorted(list(set(system_deps)))

        logger.info(f"Inferred system dependencies: {system_deps}")
        return system_deps

    def _get_current_commit(self, repo_path: Path) -> str:
        """Get the current git commit SHA."""
        import subprocess

        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=repo_path,
                capture_output=True,
                check=True,
                text=True,
            )
            commit = result.stdout.strip()
            logger.info(f"Current commit: {commit}")
            return commit
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to get commit SHA: {e}")
            return "unknown"
