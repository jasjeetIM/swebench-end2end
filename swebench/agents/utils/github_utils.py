"""
GitHub repository utilities for fetching and analyzing repositories.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, List
import logging

logger = logging.getLogger(__name__)


class GitHubRepoFetcher:
    """
    Fetches and manages GitHub repositories for analysis.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the repo fetcher.

        Args:
            cache_dir: Directory to cache cloned repos (default: /tmp/swebench-agent-repos)
        """
        self.cache_dir = cache_dir or Path(tempfile.gettempdir()) / "swebench-agent-repos"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Repo cache directory: {self.cache_dir}")

    def parse_repo_url(self, repo_url: str) -> Dict[str, str]:
        """
        Parse a GitHub repository URL.

        Args:
            repo_url: GitHub URL (https://github.com/owner/repo or owner/repo)

        Returns:
            {
                "owner": str,
                "repo": str,
                "full_name": "owner/repo",
                "clone_url": "https://github.com/owner/repo.git"
            }
        """
        # Handle different URL formats
        if repo_url.startswith("http"):
            # https://github.com/owner/repo or https://github.com/owner/repo.git
            # Remove trailing slash and .git suffix properly
            url = repo_url.rstrip("/")
            if url.endswith(".git"):
                url = url[:-4]  # Remove .git suffix
            parts = url.split("/")
            owner = parts[-2]
            repo = parts[-1]
        else:
            # owner/repo format
            parts = repo_url.split("/")
            if len(parts) != 2:
                raise ValueError(f"Invalid repo format: {repo_url}")
            owner, repo = parts

        return {
            "owner": owner,
            "repo": repo,
            "full_name": f"{owner}/{repo}",
            "clone_url": f"https://github.com/{owner}/{repo}.git",
        }

    def clone_repo(
        self, repo_url: str, commit: Optional[str] = None, shallow: bool = True
    ) -> Path:
        """
        Clone a GitHub repository.

        Args:
            repo_url: GitHub repository URL
            commit: Specific commit SHA to checkout (optional)
            shallow: Use shallow clone for faster fetching (default: True)

        Returns:
            Path to the cloned repository
        """
        repo_info = self.parse_repo_url(repo_url)
        full_name = repo_info["full_name"]
        clone_url = repo_info["clone_url"]

        # Create a unique directory for this repo
        repo_dir = self.cache_dir / full_name.replace("/", "__")

        # Check if already cloned
        if repo_dir.exists() and (repo_dir / ".git").exists():
            logger.info(f"Repository already cloned at {repo_dir}")

            # If commit specified, checkout that commit
            if commit:
                try:
                    subprocess.run(
                        ["git", "checkout", commit],
                        cwd=repo_dir,
                        check=True,
                        capture_output=True,
                    )
                    logger.info(f"Checked out commit {commit}")
                except subprocess.CalledProcessError as e:
                    logger.warning(f"Failed to checkout {commit}: {e}")

            return repo_dir

        # Clone the repository
        logger.info(f"Cloning {clone_url} to {repo_dir}")

        try:
            if shallow and not commit:
                # Shallow clone (faster)
                subprocess.run(
                    ["git", "clone", "--depth=1", clone_url, str(repo_dir)],
                    check=True,
                    capture_output=True,
                )
            else:
                # Full clone (needed for specific commits)
                subprocess.run(
                    ["git", "clone", clone_url, str(repo_dir)],
                    check=True,
                    capture_output=True,
                )

                if commit:
                    subprocess.run(
                        ["git", "checkout", commit],
                        cwd=repo_dir,
                        check=True,
                        capture_output=True,
                    )

            logger.info(f"Successfully cloned repository to {repo_dir}")
            return repo_dir

        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to clone repository: {e}")
            raise RuntimeError(f"Git clone failed: {e.stderr.decode() if e.stderr else str(e)}")

    def get_file_content(self, repo_path: Path, file_path: str) -> Optional[str]:
        """
        Read a file from the repository.

        Args:
            repo_path: Path to the cloned repository
            file_path: Relative path to the file within the repo

        Returns:
            File content as string, or None if file doesn't exist
        """
        full_path = repo_path / file_path
        if not full_path.exists():
            return None

        try:
            return full_path.read_text(encoding="utf-8")
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
            return None

    def find_files(self, repo_path: Path, pattern: str) -> List[Path]:
        """
        Find files matching a pattern in the repository.

        Args:
            repo_path: Path to the cloned repository
            pattern: Glob pattern (e.g., "*.json", "**/*.ts")

        Returns:
            List of matching file paths
        """
        return list(repo_path.glob(pattern))

    def get_repo_structure(self, repo_path: Path, max_depth: int = 2) -> Dict:
        """
        Get a summary of the repository structure.

        Args:
            repo_path: Path to the cloned repository
            max_depth: Maximum directory depth to traverse

        Returns:
            Dictionary with repository structure info
        """
        structure = {
            "root_files": [],
            "directories": [],
            "has_typescript": False,
            "has_tests": False,
        }

        # Check root files
        for item in repo_path.iterdir():
            if item.is_file():
                structure["root_files"].append(item.name)
            elif item.is_dir() and not item.name.startswith("."):
                structure["directories"].append(item.name)

        # Check for TypeScript
        ts_files = list(repo_path.glob("**/*.ts"))
        structure["has_typescript"] = len(ts_files) > 0

        # Check for tests
        test_dirs = ["test", "tests", "__tests__", "spec"]
        for test_dir in test_dirs:
            if (repo_path / test_dir).exists():
                structure["has_tests"] = True
                break

        return structure
