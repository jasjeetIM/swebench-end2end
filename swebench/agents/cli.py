"""
Command-line interface for the SWE-bench agent system.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from .orchestrator import run_agent_workflow
from .models.state_model import AgentState


def setup_logging(verbose: bool = False):
    """
    Set up logging configuration.

    Args:
        verbose: Enable verbose logging
    """
    level = logging.DEBUG if verbose else logging.INFO

    # Create logs directory
    log_dir = Path("logs/agent")
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure logging
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / "agent.log"),
        ],
    )


def print_summary(state: AgentState):
    """
    Print a summary of the workflow results.

    Args:
        state: Final agent state
    """
    print("\n" + "=" * 70)
    print("WORKFLOW SUMMARY")
    print("=" * 70)

    print(f"\nRepository: {state['repo_name']}")
    print(f"Workflow ID: {state['workflow_id']}")
    print(f"Timestamp: {state['timestamp']}")

    # Repository Analysis
    print("\n--- Repository Analysis ---")
    if state.get("repo_analysis_complete"):
        repo_model = state.get("repo_model", {})
        print(f"✓ Complete")
        print(f"  Language: {repo_model.get('language')}")
        print(f"  Package Manager: {repo_model.get('package_manager')}")
        print(f"  Node Version: {repo_model.get('node_version')}")
        print(f"  Test Framework: {repo_model.get('test_framework')}")
        print(f"  System Deps: {len(repo_model.get('system_deps', []))} packages")
    else:
        print("✗ Failed or incomplete")

    # Configuration Generation
    print("\n--- Configuration Generation ---")
    if state.get("config_generation_complete"):
        config_model = state.get("config_model", {})
        print(f"✓ Complete")
        print(f"  Version: {config_model.get('version')}")
        print(f"  Install Commands: {len(config_model.get('install', []))}")
        print(f"  Test Command: {config_model.get('test_cmd')}")
        print(f"  Build Commands: {len(config_model.get('build', []) or [])}")
        print(f"  APT Packages: {len(config_model.get('apt_pkgs', []))}")
    else:
        print("✗ Failed or incomplete")

    # Docker Validation
    print("\n--- Docker Validation ---")
    if state.get("validation_complete"):
        if state.get("validation_success"):
            print(f"✓ Success")
            print(f"  Iterations: {state['iteration_count']}/{state['max_iterations']}")
            print(f"  Test Instance: {state.get('test_instance_id')}")
        else:
            print(f"✗ Failed")
            print(f"  Iterations: {state['iteration_count']}/{state['max_iterations']}")
            print(f"  Validation Logs:")
            for log in state.get("validation_logs", []):
                print(f"    {log}")
    else:
        print("✗ Not started or incomplete")

    # Errors
    if state.get("error_occurred"):
        print("\n--- Errors ---")
        print(f"Stage: {state.get('error_stage')}")
        print(f"Message: {state.get('error_message')}")

    # Final Status
    print("\n" + "=" * 70)
    if state.get("validation_success"):
        print("STATUS: ✓ SUCCESS")
        print(f"\nConfiguration saved to: swebench/harness/constants/typescript.py")
    elif state.get("error_occurred"):
        print(f"STATUS: ✗ ERROR in {state.get('error_stage')} stage")
    else:
        print("STATUS: ✗ FAILED")

    print("=" * 70 + "\n")


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="SWE-bench Agent System - Automated Docker Configuration",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze and configure a TypeScript repo
  python -m swebench.agents.cli \\
    --repo-url https://github.com/microsoft/TypeScript \\
    --repo-name microsoft/TypeScript \\
    --version 5.3.0

  # With specific commit
  python -m swebench.agents.cli \\
    --repo-url https://github.com/vuejs/core \\
    --repo-name vuejs/core \\
    --version 3.4.0 \\
    --base-commit abc123def456

  # With custom settings
  python -m swebench.agents.cli \\
    --repo-url https://github.com/axios/axios \\
    --repo-name axios/axios \\
    --max-iterations 10 \\
    --verbose
        """,
    )

    # Required arguments
    parser.add_argument(
        "--repo-url",
        type=str,
        required=True,
        help="GitHub repository URL (e.g., https://github.com/owner/repo)",
    )
    parser.add_argument(
        "--repo-name",
        type=str,
        required=True,
        help="Repository name in format 'owner/repo'",
    )

    # Optional arguments
    parser.add_argument(
        "--language",
        type=str,
        default="typescript",
        choices=["typescript", "javascript"],
        help="Programming language (default: typescript)",
    )
    parser.add_argument(
        "--version",
        type=str,
        default="latest",
        help="Version string for configuration (default: latest)",
    )
    parser.add_argument(
        "--base-commit",
        type=str,
        default=None,
        help="Git commit SHA to analyze (optional)",
    )
    parser.add_argument(
        "--max-iterations",
        type=int,
        default=5,
        help="Maximum validation iterations (default: 5)",
    )
    parser.add_argument(
        "--cache-dir",
        type=Path,
        default=None,
        help="Directory to cache cloned repositories (optional)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(verbose=args.verbose)

    # Print header
    print("\n" + "=" * 70)
    print("SWE-bench Agent System - Automated Docker Configuration")
    print("=" * 70)
    print(f"\nRepository: {args.repo_name}")
    print(f"Language: {args.language}")
    print(f"Version: {args.version}")
    if args.base_commit:
        print(f"Commit: {args.base_commit}")
    print("")

    # Run workflow
    try:
        state = run_agent_workflow(
            repo_url=args.repo_url,
            repo_name=args.repo_name,
            language=args.language,
            version=args.version,
            base_commit=args.base_commit,
            max_iterations=args.max_iterations,
            cache_dir=args.cache_dir,
        )

        # Print summary
        print_summary(state)

        # Exit code
        if state.get("validation_success"):
            sys.exit(0)
        else:
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nWorkflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n\nFATAL ERROR: {e}")
        logging.exception("Fatal error in workflow")
        sys.exit(1)


if __name__ == "__main__":
    main()
