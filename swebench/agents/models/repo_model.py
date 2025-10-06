"""
Repository Model - Structured representation of a repository's metadata.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RepoModel:
    """
    Structured representation of a repository for Docker configuration.

    This model captures all necessary information extracted from a repository
    to generate appropriate Docker configurations.
    """

    # Basic repository info
    repo: str  # Format: "owner/repo"
    language: str  # "typescript", "javascript", etc.
    base_commit: str  # Git commit SHA to use

    # Package manager info
    package_manager: str  # "npm", "yarn", "pnpm"
    lock_file_type: Optional[str] = None  # "package-lock.json", "yarn.lock", "pnpm-lock.yaml"

    # Node.js version
    node_version: str = "20"  # Default to Node 20
    node_version_source: str = "default"  # "nvmrc", "package.json", "default"

    # Commands
    install_command: List[str] = field(default_factory=list)
    build_command: Optional[str] = None
    test_command: str = "npm test"

    # Dependencies
    dependencies: Dict[str, str] = field(default_factory=dict)
    dev_dependencies: Dict[str, str] = field(default_factory=dict)

    # Test framework
    test_framework: Optional[str] = None  # "jest", "vitest", "mocha", etc.

    # System dependencies (inferred from package dependencies)
    system_deps: List[str] = field(default_factory=list)

    # Environment variables
    env_vars: Dict[str, str] = field(default_factory=dict)

    # Build configuration
    has_typescript: bool = False
    has_build_step: bool = False

    # Additional metadata
    package_json_path: str = "package.json"
    repo_url: str = ""

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "repo": self.repo,
            "language": self.language,
            "base_commit": self.base_commit,
            "package_manager": self.package_manager,
            "lock_file_type": self.lock_file_type,
            "node_version": self.node_version,
            "node_version_source": self.node_version_source,
            "install_command": self.install_command,
            "build_command": self.build_command,
            "test_command": self.test_command,
            "dependencies": self.dependencies,
            "dev_dependencies": self.dev_dependencies,
            "test_framework": self.test_framework,
            "system_deps": self.system_deps,
            "env_vars": self.env_vars,
            "has_typescript": self.has_typescript,
            "has_build_step": self.has_build_step,
            "package_json_path": self.package_json_path,
            "repo_url": self.repo_url,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "RepoModel":
        """Create RepoModel from dictionary."""
        return cls(**data)
