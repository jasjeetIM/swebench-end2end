"""
Error Analyzer - Analyzes Docker build and test logs to identify failures.
"""

import re
from pathlib import Path
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)


class ErrorAnalyzer:
    """
    Analyzes Docker build and test execution logs to identify errors
    and suggest fixes.
    """

    # Error patterns for build failures
    BUILD_ERROR_PATTERNS = {
        "missing_package": re.compile(r"E: Unable to locate package (\S+)"),
        "node_not_found": re.compile(r"node: (not found|command not found)"),
        "npm_not_found": re.compile(r"npm: (not found|command not found)"),
        "permission_denied": re.compile(r"(EACCES|Permission denied)"),
        "network_timeout": re.compile(r"(network timeout|ETIMEDOUT|ECONNREFUSED)"),
    }

    # Error patterns for install failures
    INSTALL_ERROR_PATTERNS = {
        "missing_module": re.compile(r"Cannot find module '([^']+)'"),
        "npm_error": re.compile(r"npm ERR! (.+)"),
        "version_conflict": re.compile(r"ERESOLVE unable to resolve dependency tree"),
        "missing_python": re.compile(r"python.*not found"),
        "gyp_error": re.compile(r"gyp ERR!"),
        "missing_binary": re.compile(r"(command not found|cannot execute binary file)"),
    }

    # Error patterns for test failures (for context, not validation failures)
    TEST_ERROR_PATTERNS = {
        "timeout": re.compile(r"Timeout (error|exceeded)"),
        "chromium_missing": re.compile(r"(Chromium|Chrome).*not found"),
        "display_error": re.compile(r"(DISPLAY|X11|xvfb)"),
    }

    @staticmethod
    def analyze_build_log(log_path: Path) -> Dict:
        """
        Analyze Docker build log for errors.

        Args:
            log_path: Path to build_image.log

        Returns:
            {
                "error_type": str or None,
                "error_message": str,
                "suggested_fix": Dict,
                "log_snippets": List[str]
            }
        """
        if not log_path.exists():
            return {
                "error_type": "log_not_found",
                "error_message": f"Build log not found: {log_path}",
                "suggested_fix": {},
                "log_snippets": [],
            }

        try:
            log_content = log_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "error_type": "log_read_error",
                "error_message": f"Failed to read log: {e}",
                "suggested_fix": {},
                "log_snippets": [],
            }

        analysis = {
            "error_type": None,
            "error_message": "",
            "suggested_fix": {},
            "log_snippets": [],
        }

        # Check if build succeeded
        if "Image built successfully" in log_content:
            return analysis

        # Extract error context (last 100 lines)
        lines = log_content.split("\n")
        error_context = "\n".join(lines[-100:])
        analysis["log_snippets"].append(error_context)

        # Pattern matching
        for error_type, pattern in ErrorAnalyzer.BUILD_ERROR_PATTERNS.items():
            match = pattern.search(log_content)
            if match:
                analysis["error_type"] = error_type

                if error_type == "missing_package":
                    package = match.group(1)
                    analysis["error_message"] = f"Missing system package: {package}"
                    analysis["suggested_fix"] = {
                        "fix_type": "remove_apt_package",
                        "field": "apt_pkgs",
                        "value": package,
                        "reason": "Package not found in apt repositories",
                    }

                elif error_type in ["node_not_found", "npm_not_found"]:
                    analysis["error_message"] = "Node.js installation failed"
                    analysis["suggested_fix"] = {
                        "fix_type": "change_version",
                        "field": "node_version",
                        "value": "18",
                        "reason": "Fallback to stable Node version",
                    }

                elif error_type == "network_timeout":
                    analysis["error_message"] = "Network timeout during build"
                    analysis["suggested_fix"] = {
                        "fix_type": "retry",
                        "reason": "Transient network error",
                    }

                break

        # Check for generic build failure
        if "Error building image" in log_content and not analysis["error_type"]:
            analysis["error_type"] = "build_failure_generic"
            analysis["error_message"] = "Docker build failed (unknown cause)"

        return analysis

    @staticmethod
    def analyze_test_output(log_path: Path) -> Dict:
        """
        Analyze test execution output for errors.

        Args:
            log_path: Path to test_output.txt

        Returns:
            Analysis dict similar to analyze_build_log
        """
        if not log_path.exists():
            return {
                "error_type": "log_not_found",
                "error_message": f"Test output not found: {log_path}",
                "suggested_fix": {},
                "log_snippets": [],
            }

        try:
            log_content = log_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "error_type": "log_read_error",
                "error_message": f"Failed to read log: {e}",
                "suggested_fix": {},
                "log_snippets": [],
            }

        analysis = {
            "error_type": None,
            "error_message": "",
            "suggested_fix": {},
            "log_snippets": [],
        }

        # Check for install failure
        if ">>>>> Init Failed" in log_content or "INSTALL_FAIL" in log_content:
            analysis["error_type"] = "install_failure"

            # Extract install error section
            error_start = log_content.find(">>>>> Init Failed")
            if error_start != -1:
                error_section = log_content[error_start : error_start + 2000]
                analysis["log_snippets"].append(error_section)

            # Pattern matching for install errors
            for error_type, pattern in ErrorAnalyzer.INSTALL_ERROR_PATTERNS.items():
                match = pattern.search(log_content)
                if match:
                    if error_type == "missing_module":
                        module = match.group(1)
                        analysis["error_message"] = f"Missing module: {module}"
                        analysis["suggested_fix"] = {
                            "fix_type": "add_command",
                            "field": "install",
                            "value": f"npm install {module}",
                            "reason": f"Module {module} not found",
                        }

                    elif error_type == "version_conflict":
                        analysis["error_message"] = "Dependency version conflict"
                        analysis["suggested_fix"] = {
                            "fix_type": "add_npm_flag",
                            "field": "install",
                            "value": "--legacy-peer-deps",
                            "reason": "Resolve peer dependency conflicts",
                        }

                    elif error_type == "missing_python":
                        analysis["error_message"] = "Python not found (needed for native modules)"
                        analysis["suggested_fix"] = {
                            "fix_type": "add_apt_package",
                            "field": "apt_pkgs",
                            "value": "python3",
                            "reason": "Required for node-gyp",
                        }

                    elif error_type == "gyp_error":
                        analysis["error_message"] = "node-gyp compilation error"
                        analysis["suggested_fix"] = {
                            "fix_type": "add_apt_package",
                            "field": "apt_pkgs",
                            "value": "build-essential",
                            "reason": "Required for native module compilation",
                        }

                    break

        # Check if tests actually ran (success for validation purposes)
        elif any(
            marker in log_content
            for marker in ["npm test", "jest", "mocha", "vitest", "Test Suites"]
        ):
            # Tests ran - that's good enough for validation
            analysis["error_type"] = None
            return analysis

        # Check for test execution errors
        for error_type, pattern in ErrorAnalyzer.TEST_ERROR_PATTERNS.items():
            match = pattern.search(log_content)
            if match:
                analysis["error_type"] = error_type

                if error_type == "chromium_missing":
                    analysis["error_message"] = "Chromium browser not found"
                    analysis["suggested_fix"] = {
                        "fix_type": "add_apt_package",
                        "field": "apt_pkgs",
                        "value": "chromium",
                        "reason": "Required for browser tests",
                    }

                elif error_type == "display_error":
                    analysis["error_message"] = "Display/X11 error"
                    analysis["suggested_fix"] = {
                        "fix_type": "add_apt_package",
                        "field": "apt_pkgs",
                        "value": "xvfb",
                        "reason": "Required for headless browser tests",
                    }

                break

        return analysis

    @staticmethod
    def analyze_run_log(log_path: Path) -> Dict:
        """
        Analyze run_instance.log for execution errors.

        Args:
            log_path: Path to run_instance.log

        Returns:
            Analysis dict
        """
        if not log_path.exists():
            return {
                "error_type": None,
                "error_message": "",
                "suggested_fix": {},
                "log_snippets": [],
            }

        try:
            log_content = log_path.read_text(encoding="utf-8")
        except Exception as e:
            return {
                "error_type": "log_read_error",
                "error_message": f"Failed to read log: {e}",
                "suggested_fix": {},
                "log_snippets": [],
            }

        analysis = {
            "error_type": None,
            "error_message": "",
            "suggested_fix": {},
            "log_snippets": [],
        }

        # Check for timeout
        if "Timeout error" in log_content:
            analysis["error_type"] = "timeout"
            analysis["error_message"] = "Test execution timed out"
            analysis["suggested_fix"] = {
                "fix_type": "increase_timeout",
                "field": "timeout",
                "value": 600,
                "reason": "Tests taking longer than expected",
            }

        return analysis

    @staticmethod
    def analyze_logs(log_dir: Path) -> Dict:
        """
        Analyze all logs in a directory and return comprehensive analysis.

        Args:
            log_dir: Directory containing logs (run_instance.log, test_output.txt, etc.)

        Returns:
            Consolidated analysis dict
        """
        analysis = {
            "error_type": None,
            "error_message": "",
            "suggested_fix": {},
            "log_snippets": [],
        }

        # 1. Check build log
        build_log_symlink = log_dir / "image_build_dir"
        if build_log_symlink.exists() and build_log_symlink.is_symlink():
            build_log_path = build_log_symlink / "build_image.log"
            if build_log_path.exists():
                build_analysis = ErrorAnalyzer.analyze_build_log(build_log_path)
                if build_analysis["error_type"]:
                    return build_analysis

        # 2. Check test output
        test_output_path = log_dir / "test_output.txt"
        if test_output_path.exists():
            test_analysis = ErrorAnalyzer.analyze_test_output(test_output_path)
            if test_analysis["error_type"]:
                return test_analysis

            # If no error type but also no test execution, that's suspicious
            if not test_analysis["error_type"]:
                # Tests ran successfully - validation passed!
                return analysis

        # 3. Check run log
        run_log_path = log_dir / "run_instance.log"
        if run_log_path.exists():
            run_analysis = ErrorAnalyzer.analyze_run_log(run_log_path)
            if run_analysis["error_type"]:
                return run_analysis

        return analysis
