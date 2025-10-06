"""
Docker Validator Agent - Validates and iteratively fixes Docker configurations.
"""

import docker
import json
from pathlib import Path
from typing import Dict, Tuple, Optional
import logging

from .models.config_model import ConfigModel
from .models.state_model import AgentState
from .utils.error_analyzer import ErrorAnalyzer
from .config_generator import ConfigGeneratorAgent

from swebench.harness.docker_build import (
    build_instance_images,
    BuildImageError,
    setup_logger,
    close_logger,
)
from swebench.harness.run_evaluation import run_instance
from swebench.harness.test_spec.test_spec import make_test_spec
from swebench.harness.constants import (
    INSTANCE_IMAGE_BUILD_DIR,
    RUN_EVALUATION_LOG_DIR,
)

logger = logging.getLogger(__name__)


class DockerValidatorAgent:
    """
    Agent responsible for validating Docker configurations through
    iterative build-test-fix cycles.
    """

    def __init__(self, max_iterations: int = 5):
        """
        Initialize the Docker Validator Agent.

        Args:
            max_iterations: Maximum number of validation iterations
        """
        self.max_iterations = max_iterations
        self.client = docker.from_env()
        self.error_analyzer = ErrorAnalyzer()
        self.config_generator = ConfigGeneratorAgent()
        logger.info(f"DockerValidatorAgent initialized (max_iterations={max_iterations})")

    def validate(self, state: AgentState) -> AgentState:
        """
        Validate Docker configuration with iterative fixes.

        This is the main entry point called by the LangGraph workflow.

        Args:
            state: Current agent state with config_model

        Returns:
            Updated agent state with validation results
        """
        try:
            if not state.get("config_generation_complete"):
                raise ValueError("Configuration generation not complete")

            if not state.get("config_model"):
                raise ValueError("config_model not found in state")

            logger.info(f"Starting validation for: {state['repo_name']}")

            # Convert dict to ConfigModel
            config_model = ConfigModel.from_dict(state["config_model"])

            # Create test instance (injects specs into constants)
            test_instance = self._create_test_instance(state, config_model)

            # Run validation loop
            success, final_config, iteration_logs = self._validation_loop(
                config_model, test_instance, state
            )

            # Update state
            state["config_model"] = final_config.to_dict()
            state["validation_complete"] = True
            state["validation_success"] = success
            state["validation_logs"] = iteration_logs
            state["test_instance_id"] = test_instance["instance_id"]

            if success:
                logger.info("✓ Validation succeeded!")
            else:
                logger.warning("✗ Validation failed after max iterations")

            return state

        except Exception as e:
            logger.error(f"Error during validation: {e}", exc_info=True)
            state["error_occurred"] = True
            state["error_message"] = str(e)
            state["error_stage"] = "validate"
            return state

    def _create_test_instance(self, state: AgentState, config_model: ConfigModel) -> Dict:
        """
        Create a synthetic SWE-bench instance for validation.

        IMPORTANT: We inject the specs directly into MAP_REPO_VERSION_TO_SPECS
        to avoid module reload issues. This is done before calling make_test_spec.

        Args:
            state: Current agent state
            config_model: Configuration model with specs

        Returns:
            SWE-bench instance dict
        """
        repo_model_dict = state["repo_model"]
        instance_id = f"{state['repo_name'].replace('/', '__')}-agent-test-{state['version']}"

        # CRITICAL: Inject specs into the imported MAP_REPO_VERSION_TO_SPECS
        # This ensures make_test_spec() can find our newly created config
        from swebench.harness import constants

        repo_name = state["repo_name"]
        version = state["version"]

        # Add repo to MAP_REPO_VERSION_TO_SPECS if not present
        if repo_name not in constants.MAP_REPO_VERSION_TO_SPECS:
            constants.MAP_REPO_VERSION_TO_SPECS[repo_name] = {}

        # Add version specs
        constants.MAP_REPO_VERSION_TO_SPECS[repo_name][version] = config_model.to_constants_entry()

        # Also add to MAP_REPO_TO_EXT for language detection
        constants.MAP_REPO_TO_EXT[repo_name] = "ts" if state["language"] == "typescript" else "js"

        logger.info(f"Injected specs into MAP_REPO_VERSION_TO_SPECS for {repo_name}:{version}")

        instance = {
            "instance_id": instance_id,
            "repo": repo_name,
            "version": version,
            "base_commit": repo_model_dict["base_commit"],
            "problem_statement": "Docker configuration validation test",
            "hints_text": "",
            "test_patch": "",
            "FAIL_TO_PASS": "[]",
            "PASS_TO_PASS": "[]",
            "created_at": state["timestamp"],
            "environment_setup_commit": repo_model_dict["base_commit"],
            "patch": "",
        }

        logger.info(f"Created test instance: {instance_id}")
        return instance

    def _validation_loop(
        self, initial_config: ConfigModel, test_instance: Dict, state: AgentState
    ) -> Tuple[bool, ConfigModel, list[str]]:
        """
        Main validation loop with iterative fixes.

        Args:
            initial_config: Initial configuration
            test_instance: Test instance dict
            state: Agent state

        Returns:
            (success: bool, final_config: ConfigModel, iteration_logs: List[str])
        """
        config_model = initial_config
        iteration_logs = []

        for iteration in range(1, self.max_iterations + 1):
            logger.info(f"\n{'=' * 60}")
            logger.info(f"ITERATION {iteration}/{self.max_iterations}")
            logger.info(f"{'=' * 60}\n")

            state["iteration_count"] = iteration

            # Step 1 & 2: Write configuration files
            try:
                self._write_configuration_files(config_model)
            except Exception as e:
                error_msg = f"Failed to write config files: {e}"
                logger.error(error_msg)
                iteration_logs.append(f"Iteration {iteration}: {error_msg}")
                return False, config_model, iteration_logs

            # Step 3: Build Docker images
            build_success, build_log_path = self._build_images(test_instance)

            if not build_success:
                logger.error(f"Build failed on iteration {iteration}")
                iteration_logs.append(f"Iteration {iteration}: Build failed")

                # Analyze build failure
                analysis = self._analyze_failure(Path(build_log_path), "build")

                if not analysis.get("suggested_fix"):
                    error_msg = f"No fix suggested for build failure: {analysis['error_message']}"
                    logger.error(error_msg)
                    iteration_logs.append(f"Iteration {iteration}: {error_msg}")
                    return False, config_model, iteration_logs

                # Apply fix and retry
                self._apply_fix(config_model, analysis["suggested_fix"])
                continue

            # Step 4: Run test instance
            run_success, log_dir = self._run_test_instance(test_instance)

            # Step 5: Analyze results
            analysis = self.error_analyzer.analyze_logs(log_dir)

            # Check success
            if analysis["error_type"] is None:
                logger.info(f"✓ Validation succeeded on iteration {iteration}!")
                iteration_logs.append(f"Iteration {iteration}: Success!")
                return True, config_model, iteration_logs

            # Failed - log and attempt fix
            error_msg = f"{analysis['error_type']}: {analysis['error_message']}"
            logger.warning(f"Test failed: {error_msg}")
            iteration_logs.append(f"Iteration {iteration}: {error_msg}")

            if not analysis.get("suggested_fix"):
                logger.error(f"No fix suggested for: {error_msg}")
                return False, config_model, iteration_logs

            # Apply fix and continue
            self._apply_fix(config_model, analysis["suggested_fix"])

        # Max iterations reached
        logger.error(f"Failed after {self.max_iterations} iterations")
        iteration_logs.append(f"Max iterations ({self.max_iterations}) reached")
        return False, config_model, iteration_logs

    def _write_configuration_files(self, config_model: ConfigModel) -> None:
        """
        Write configuration files to harness/constants and update dockerfiles.

        Args:
            config_model: Configuration to write
        """
        # Write TypeScript constants
        constants_path = Path("swebench/harness/constants/typescript.py")
        self.config_generator.write_constants_file(config_model, constants_path)

        # Update constants __init__.py to import TypeScript
        self._update_constants_init()

        # Update dockerfiles __init__.py to support TypeScript
        self._update_dockerfiles_init()

        logger.info("Configuration files written successfully")

    def _update_constants_init(self) -> None:
        """Update harness/constants/__init__.py to import TypeScript constants."""
        init_path = Path("swebench/harness/constants/__init__.py")

        if not init_path.exists():
            logger.warning(f"{init_path} not found")
            return

        content = init_path.read_text()

        # Check if already imported
        if "from swebench.harness.constants.typescript import *" in content:
            logger.info("TypeScript already imported in constants/__init__.py")
            return

        # Add import after other language imports
        import_line = "from swebench.harness.constants.typescript import *\n"

        # Find where to insert (after last language import)
        lines = content.split("\n")
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("from swebench.harness.constants."):
                insert_idx = i + 1

        lines.insert(insert_idx, import_line.strip())

        # Also update the aggregate maps
        # Find MAP_REPO_VERSION_TO_SPECS and add TypeScript
        for i, line in enumerate(lines):
            if line.strip() == "MAP_REPO_VERSION_TO_SPECS = {":
                # Find the closing brace
                for j in range(i + 1, len(lines)):
                    if lines[j].strip() == "}":
                        # Insert before closing brace
                        lines.insert(j, "    **MAP_REPO_VERSION_TO_SPECS_TS,")
                        break
                break

        # Write back
        init_path.write_text("\n".join(lines))
        logger.info("Updated constants/__init__.py")

    def _update_dockerfiles_init(self) -> None:
        """Update harness/dockerfiles/__init__.py to support TypeScript."""
        init_path = Path("swebench/harness/dockerfiles/__init__.py")

        if not init_path.exists():
            logger.warning(f"{init_path} not found")
            return

        content = init_path.read_text()

        # Check if already updated
        if 'from . import javascript as js' in content:
            logger.info("JavaScript already imported in dockerfiles/__init__.py")

            # Just need to update the functions to support ts/js
            # This is a simple patch - in production you'd want more robust code
            if 'elif language in ["js", "ts"]:' not in content:
                # Replace the py-only check with multi-language support
                old_check = 'if language != "py":\n        raise ValueError(f"Unsupported language: {language}")'
                new_check = '''if language == "py":
        return_code = "py specific"
    elif language in ["js", "ts"]:
        from . import javascript as js
        return_code = "js specific"
    else:
        raise ValueError(f"Unsupported language: {language}")'''

                # This is simplified - actual implementation would need proper replacement
                logger.info("dockerfiles/__init__.py needs manual update for multi-language support")

            return

        # Add import
        import_line = "from . import javascript as js\n"
        lines = content.split("\n")

        # Add after python import
        for i, line in enumerate(lines):
            if line.strip() == "from . import python as py":
                lines.insert(i + 1, import_line.strip())
                break

        # Write back
        init_path.write_text("\n".join(lines))
        logger.info("Updated dockerfiles/__init__.py")

    def _build_images(self, test_instance: Dict) -> Tuple[bool, str]:
        """
        Build Docker images for the test instance.

        Args:
            test_instance: Test instance dict

        Returns:
            (success: bool, log_path: str)
        """
        try:
            logger.info(f"Building images for {test_instance['instance_id']}")

            dataset = [test_instance]
            print(test_instance)

            successful, failed = build_instance_images(
                client=self.client,
                dataset=dataset,
                force_rebuild=True,
                max_workers=1,
                namespace=None,
                tag="agent-test",
                env_image_tag="agent-test",
            )

            if failed:
                # Get build log path
                instance_id = test_instance["instance_id"]
                log_dir = (
                    INSTANCE_IMAGE_BUILD_DIR
                    / f"sweb.eval.x86_64.{instance_id.lower()}__agent-test"
                )
                build_log_path = log_dir / "build_image.log"

                if build_log_path.exists():
                    logger.error(f"Build failed, log at: {build_log_path}")
                    return False, str(build_log_path)
                else:
                    return False, "Build log not found"

            logger.info("✓ Images built successfully")
            return True, ""

        except BuildImageError as e:
            logger.error(f"BuildImageError: {e}")
            return False, str(e.log_path)
        except Exception as e:
            logger.error(f"Unexpected build error: {e}", exc_info=True)
            return False, str(e)

    def _run_test_instance(self, test_instance: Dict) -> Tuple[bool, Path]:
        """
        Run the test instance.

        Args:
            test_instance: Test instance dict

        Returns:
            (success: bool, log_dir: Path)
        """
        instance_id = test_instance["instance_id"]

        try:
            # Create TestSpec
            test_spec = make_test_spec(
                test_instance,
                namespace=None,
                instance_image_tag="agent-test",
                env_image_tag="agent-test",
            )

            # Create dummy prediction
            pred = {
                "instance_id": instance_id,
                "model_name_or_path": "agent-validator",
                "model_patch": "",
            }

            logger.info(f"Running test instance {instance_id}")

            result = run_instance(
                test_spec=test_spec,
                pred=pred,
                rm_image=False,
                force_rebuild=False,
                client=self.client,
                run_id="agent-validation",
                timeout=300,
                rewrite_reports=False,
            )

            log_dir = (
                RUN_EVALUATION_LOG_DIR
                / "agent-validation"
                / "agent-validator"
                / instance_id
            )

            success = result.get("completed", False)
            logger.info(f"Test instance result: completed={success}")

            return success, log_dir

        except Exception as e:
            logger.error(f"Error running test instance: {e}", exc_info=True)
            # Return log dir even on error for analysis
            log_dir = (
                RUN_EVALUATION_LOG_DIR
                / "agent-validation"
                / "agent-validator"
                / instance_id
            )
            return False, log_dir

    def _analyze_failure(self, log_path: Path, failure_type: str) -> Dict:
        """
        Analyze failure logs.

        Args:
            log_path: Path to log file
            failure_type: "build" or "test"

        Returns:
            Analysis dict with error_type, error_message, suggested_fix
        """
        if failure_type == "build":
            return self.error_analyzer.analyze_build_log(log_path)
        else:
            return self.error_analyzer.analyze_test_output(log_path)


    def _apply_fix(self, config_model: ConfigModel, fix: Dict) -> None:
        """
        Apply a suggested fix to the configuration.

        Args:
            config_model: Configuration to modify
            fix: Fix dictionary from error analysis
        """
        logger.info(f"Applying fix: {fix}")
        config_model.update_from_fix(fix)
        logger.info(f"Updated config: {config_model.to_dict()}")
