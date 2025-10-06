"""
Configuration Model - Structured representation of SWE-bench configuration.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass
class ConfigModel:
    """
    Structured representation of SWE-bench Docker configuration.

    This model represents the configuration that will be written to
    harness/constants/typescript.py and used for Docker image generation.
    """

    # Repository and version info
    repo: str  # Format: "owner/repo"
    version: str  # Version string (e.g., "5.3.0")

    # Installation configuration
    install: List[str] = field(default_factory=list)

    # Test configuration
    test_cmd: str = "npm test"

    # Optional build step
    build: Optional[List[str]] = None

    # Docker specifications
    docker_specs: Dict[str, Any] = field(default_factory=dict)

    # System packages (apt packages)
    apt_pkgs: List[str] = field(default_factory=list)

    # Environment variables
    env_vars: Dict[str, str] = field(default_factory=dict)

    def to_constants_entry(self) -> Dict:
        """
        Convert to the format expected by harness/constants/*.py

        Returns:
            Dictionary in the format:
            {
                "install": [...],
                "test_cmd": "...",
                "build": [...],  # optional
                "docker_specs": {...},
                "apt-pkgs": [...],  # optional
            }
        """
        entry = {
            "install": self.install,
            "test_cmd": self.test_cmd,
            "docker_specs": self.docker_specs,
        }

        if self.build:
            entry["build"] = self.build

        if self.apt_pkgs:
            entry["apt-pkgs"] = self.apt_pkgs

        return entry

    def to_dict(self) -> Dict:
        """Convert to dictionary representation."""
        return {
            "repo": self.repo,
            "version": self.version,
            "install": self.install,
            "test_cmd": self.test_cmd,
            "build": self.build,
            "docker_specs": self.docker_specs,
            "apt_pkgs": self.apt_pkgs,
            "env_vars": self.env_vars,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "ConfigModel":
        """Create ConfigModel from dictionary."""
        return cls(**data)

    def update_from_fix(self, fix: Dict) -> None:
        """
        Apply a fix proposed by the Docker Validator Agent.

        Args:
            fix: Dictionary with keys:
                - fix_type: "add_package", "change_version", "add_command", "add_apt_package"
                - field: Field to modify
                - value: New value
        """
        fix_type = fix.get("fix_type")
        field = fix.get("field")
        value = fix.get("value")

        if fix_type == "add_apt_package":
            if value not in self.apt_pkgs:
                self.apt_pkgs.append(value)

        elif fix_type == "remove_apt_package":
            if value in self.apt_pkgs:
                self.apt_pkgs.remove(value)

        elif fix_type == "change_version":
            if field == "node_version":
                self.docker_specs["node_version"] = value
            elif field == "pnpm_version":
                self.docker_specs["pnpm_version"] = value

        elif fix_type == "add_command":
            if field == "install":
                if value not in self.install:
                    self.install.append(value)
            elif field == "build":
                if self.build is None:
                    self.build = []
                if value not in self.build:
                    self.build.append(value)

        elif fix_type == "modify_test_cmd":
            self.test_cmd = value

        elif fix_type == "add_npm_flag":
            # Modify install commands to add npm flags
            for i, cmd in enumerate(self.install):
                if "npm install" in cmd and value not in cmd:
                    self.install[i] = f"{cmd} {value}"
