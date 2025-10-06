"""
Dependency Mapper - Maps npm packages to system dependencies.
"""

from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


class DependencyMapper:
    """
    Maps npm package dependencies to required system packages.
    """

    # Mapping of npm packages to system dependencies
    PACKAGE_TO_SYSTEM_DEPS = {
        # Browser automation
        "puppeteer": ["chromium", "libx11-xcb1", "libxcomposite1"],
        "playwright": ["chromium", "libx11-xcb1"],
        "selenium-webdriver": ["chromium"],
        # Graphics and canvas
        "canvas": [
            "pkg-config",
            "build-essential",
            "libcairo2-dev",
            "libpango1.0-dev",
            "libjpeg-dev",
            "libgif-dev",
            "librsvg2-dev",
        ],
        "node-canvas": [
            "pkg-config",
            "build-essential",
            "libcairo2-dev",
            "libpango1.0-dev",
            "libjpeg-dev",
            "libgif-dev",
        ],
        # Image processing
        "sharp": ["libvips-dev"],
        "imagemagick": ["imagemagick"],
        # PDF generation
        "pdf-lib": [],
        "pdfkit": ["libpixman-1-dev"],
        # Native modules
        "sqlite3": ["libsqlite3-dev"],
        "bcrypt": ["python3"],
        "node-gyp": ["python3", "build-essential"],
        # Video/Audio
        "ffmpeg": ["ffmpeg"],
        "node-ffmpeg": ["ffmpeg"],
        # System utilities
        "node-sass": ["libsass-dev", "sassc"],
        "sass": ["libsass-dev"],
    }

    # Dependency patterns (regex-based)
    PATTERN_TO_SYSTEM_DEPS = {
        r".*chrome.*": ["chromium"],
        r".*cairo.*": ["libcairo2-dev"],
        r".*vips.*": ["libvips-dev"],
    }

    @staticmethod
    def get_system_deps_for_package(package_name: str) -> List[str]:
        """
        Get system dependencies for a specific npm package.

        Args:
            package_name: npm package name

        Returns:
            List of system package names
        """
        # Direct mapping
        if package_name in DependencyMapper.PACKAGE_TO_SYSTEM_DEPS:
            return DependencyMapper.PACKAGE_TO_SYSTEM_DEPS[package_name].copy()

        # Pattern-based mapping
        import re

        for pattern, deps in DependencyMapper.PATTERN_TO_SYSTEM_DEPS.items():
            if re.match(pattern, package_name):
                return deps.copy()

        return []

    @staticmethod
    def get_system_deps_from_dependencies(dependencies: Dict[str, str]) -> List[str]:
        """
        Get all system dependencies from a dict of npm dependencies.

        Args:
            dependencies: Dict of package_name -> version

        Returns:
            List of unique system package names
        """
        system_deps: Set[str] = set()

        for package_name in dependencies.keys():
            deps = DependencyMapper.get_system_deps_for_package(package_name)
            system_deps.update(deps)

        return sorted(list(system_deps))

    @staticmethod
    def infer_test_framework_deps(test_framework: str) -> List[str]:
        """
        Get system dependencies for test frameworks.

        Args:
            test_framework: Name of test framework (jest, mocha, etc.)

        Returns:
            List of system package names
        """
        framework_deps = {
            "playwright": ["chromium", "libx11-xcb1"],
            "cypress": ["chromium", "xvfb"],
            # Most other test frameworks don't need system deps
        }

        return framework_deps.get(test_framework, [])

    @staticmethod
    def get_node_version_from_package_manager(package_manager: str) -> str:
        """
        Get recommended Node.js version for a package manager.

        Args:
            package_manager: Package manager name (npm, yarn, pnpm)

        Returns:
            Node.js version string
        """
        # Modern package managers work best with recent Node versions
        recommendations = {
            "pnpm": "20",
            "yarn": "20",
            "npm": "20",
        }

        return recommendations.get(package_manager, "20")

    @staticmethod
    def get_install_command(package_manager: str, flags: List[str] = None) -> List[str]:
        """
        Get install commands for a package manager.

        Args:
            package_manager: Package manager name (npm, yarn, pnpm)
            flags: Additional flags to add

        Returns:
            List of install commands
        """
        flags = flags or []
        flag_str = " ".join(flags)

        commands = {
            "npm": [f"npm install {flag_str}".strip()],
            "yarn": [f"yarn install {flag_str}".strip()],
            "pnpm": [f"pnpm install {flag_str}".strip()],
        }

        return commands.get(package_manager, ["npm install"])
