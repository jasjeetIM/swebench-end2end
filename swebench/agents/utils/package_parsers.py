"""
Parsers for package.json, tsconfig.json, and other config files.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class PackageJsonParser:
    """
    Parser for package.json files.
    """

    def __init__(self, package_json_path: Path):
        """
        Initialize the parser.

        Args:
            package_json_path: Path to package.json
        """
        self.path = package_json_path
        self.data = self._load_json()

    def _load_json(self) -> Dict:
        """Load and parse package.json."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to parse {self.path}: {e}")
            return {}

    def get_dependencies(self) -> Dict[str, str]:
        """Get production dependencies."""
        return self.data.get("dependencies", {})

    def get_dev_dependencies(self) -> Dict[str, str]:
        """Get development dependencies."""
        return self.data.get("devDependencies", {})

    def get_all_dependencies(self) -> Dict[str, str]:
        """Get all dependencies (prod + dev)."""
        deps = self.get_dependencies().copy()
        deps.update(self.get_dev_dependencies())
        return deps

    def get_scripts(self) -> Dict[str, str]:
        """Get npm scripts."""
        return self.data.get("scripts", {})

    def get_test_command(self) -> str:
        """
        Infer the test command from package.json scripts.

        Returns:
            Test command string (default: "npm test")
        """
        scripts = self.get_scripts()

        # Common test script names
        test_scripts = ["test", "test:unit", "test:all"]

        for script_name in test_scripts:
            if script_name in scripts:
                return f"npm run {script_name}"

        # Default
        return "npm test"

    def get_build_command(self) -> Optional[str]:
        """
        Infer the build command from package.json scripts.

        Returns:
            Build command string or None if no build script
        """
        scripts = self.get_scripts()

        # Common build script names
        build_scripts = ["build", "compile", "dist"]

        for script_name in build_scripts:
            if script_name in scripts:
                return f"npm run {script_name}"

        return None

    def get_node_version_from_engines(self) -> Optional[str]:
        """
        Get Node.js version from engines field.

        Returns:
            Node version string or None
        """
        engines = self.data.get("engines", {})
        node_version = engines.get("node")

        if node_version:
            # Parse version constraint (e.g., ">=14.0.0", "^16.0.0", "20.x")
            # Extract the major version number
            match = re.search(r"(\d+)", node_version)
            if match:
                return match.group(1)

        return None

    def get_package_manager(self) -> Optional[str]:
        """
        Get package manager from packageManager field.

        Returns:
            Package manager name ("npm", "yarn", "pnpm") or None
        """
        package_manager = self.data.get("packageManager", "")

        if "pnpm" in package_manager:
            return "pnpm"
        elif "yarn" in package_manager:
            return "yarn"
        elif "npm" in package_manager:
            return "npm"

        return None

    def infer_test_framework(self) -> Optional[str]:
        """
        Infer the test framework from dependencies.

        Returns:
            Test framework name or None
        """
        deps = self.get_all_dependencies()

        # Check for common test frameworks
        frameworks = {
            "jest": "jest",
            "vitest": "vitest",
            "mocha": "mocha",
            "jasmine": "jasmine",
            "ava": "ava",
            "tape": "tape",
            "@playwright/test": "playwright",
            "cypress": "cypress",
        }

        for dep, framework in frameworks.items():
            if dep in deps:
                return framework

        return None

    def has_typescript(self) -> bool:
        """Check if the project uses TypeScript."""
        deps = self.get_all_dependencies()
        return "typescript" in deps

    def get_workspace_info(self) -> Optional[Dict[str, Any]]:
        """
        Get workspace/monorepo information.

        Returns:
            Workspace info dict or None
        """
        workspaces = self.data.get("workspaces")
        if workspaces:
            return {"type": "npm", "workspaces": workspaces}

        return None


class TsConfigParser:
    """
    Parser for tsconfig.json files.
    """

    def __init__(self, tsconfig_path: Path):
        """
        Initialize the parser.

        Args:
            tsconfig_path: Path to tsconfig.json
        """
        self.path = tsconfig_path
        self.data = self._load_json()

    def _load_json(self) -> Dict:
        """Load and parse tsconfig.json (with comments removed)."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                content = f.read()

            # Remove comments (simple approach - may not handle all edge cases)
            content = re.sub(r"//.*", "", content)
            content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)

            return json.loads(content)
        except Exception as e:
            logger.warning(f"Failed to parse {self.path}: {e}")
            return {}

    def get_compiler_options(self) -> Dict[str, Any]:
        """Get TypeScript compiler options."""
        return self.data.get("compilerOptions", {})

    def get_target(self) -> Optional[str]:
        """Get TypeScript compilation target (e.g., "ES2020")."""
        return self.get_compiler_options().get("target")

    def get_module(self) -> Optional[str]:
        """Get module system (e.g., "commonjs", "esnext")."""
        return self.get_compiler_options().get("module")

    def get_out_dir(self) -> Optional[str]:
        """Get output directory for compiled files."""
        return self.get_compiler_options().get("outDir")


class LockFileDetector:
    """
    Detect package manager from lock files.
    """

    @staticmethod
    def detect_lock_file(repo_path: Path) -> Optional[str]:
        """
        Detect which lock file exists in the repository.

        Args:
            repo_path: Path to the repository

        Returns:
            Lock file name or None
        """
        lock_files = {
            "pnpm-lock.yaml": "pnpm",
            "yarn.lock": "yarn",
            "package-lock.json": "npm",
        }

        for lock_file, package_manager in lock_files.items():
            if (repo_path / lock_file).exists():
                return package_manager

        return None
