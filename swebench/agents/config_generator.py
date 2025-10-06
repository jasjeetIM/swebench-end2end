"""
Config Generator Agent - Generates SWE-bench configuration from RepoModel.
"""

from pathlib import Path
from typing import Dict, Optional
import logging

from .models.repo_model import RepoModel
from .models.config_model import ConfigModel
from .models.state_model import AgentState

logger = logging.getLogger(__name__)


class ConfigGeneratorAgent:
    """
    Agent responsible for generating SWE-bench Docker configurations.
    """

    def __init__(self):
        """Initialize the Config Generator Agent."""
        logger.info("ConfigGeneratorAgent initialized")

    def generate(self, state: AgentState) -> AgentState:
        """
        Generate Docker configuration from repo analysis.

        This is the main entry point called by the LangGraph workflow.

        Args:
            state: Current agent state with repo_model

        Returns:
            Updated agent state with config_model populated
        """
        try:
            if not state.get("repo_analysis_complete"):
                raise ValueError("Repository analysis not complete")

            if not state.get("repo_model"):
                raise ValueError("repo_model not found in state")

            logger.info(f"Generating config for: {state['repo_name']}")

            # Convert dict back to RepoModel
            repo_model = RepoModel.from_dict(state["repo_model"])

            # Generate configuration
            config_model = self._generate_config(repo_model, state)

            # Update state
            state["config_model"] = config_model.to_dict()
            state["config_generation_complete"] = True

            logger.info(f"Configuration generation complete")
            return state

        except Exception as e:
            logger.error(f"Error generating configuration: {e}", exc_info=True)
            state["error_occurred"] = True
            state["error_message"] = str(e)
            state["error_stage"] = "generate"
            return state

    def _generate_config(self, repo_model: RepoModel, state: AgentState) -> ConfigModel:
        """
        Generate ConfigModel from RepoModel.

        Args:
            repo_model: Repository analysis results
            state: Current agent state

        Returns:
            ConfigModel with Docker configuration
        """
        # Determine install commands
        install_commands = self._generate_install_commands(repo_model)

        # Determine test command
        test_command = repo_model.test_command

        # Determine build commands (optional)
        build_commands = self._generate_build_commands(repo_model)

        # Generate docker_specs
        docker_specs = self._generate_docker_specs(repo_model)

        # Get system packages
        apt_pkgs = repo_model.system_deps.copy()

        # Create ConfigModel
        config_model = ConfigModel(
            repo=repo_model.repo,
            version=state["version"],
            install=install_commands,
            test_cmd=test_command,
            build=build_commands,
            docker_specs=docker_specs,
            apt_pkgs=apt_pkgs,
            env_vars=repo_model.env_vars.copy(),
        )

        logger.info(f"Generated config: {config_model.to_dict()}")
        return config_model

    def _generate_install_commands(self, repo_model: RepoModel) -> list[str]:
        """
        Generate installation commands based on package manager.

        Args:
            repo_model: Repository model

        Returns:
            List of install commands
        """
        commands = []

        # Base install command
        base_cmd = repo_model.install_command[0] if repo_model.install_command else "npm install"

        # Add any special flags based on package manager
        if repo_model.package_manager == "pnpm":
            # pnpm might need specific flags
            commands.append(base_cmd)
        elif repo_model.package_manager == "yarn":
            commands.append(base_cmd)
        else:  # npm
            commands.append(base_cmd)

        logger.info(f"Install commands: {commands}")
        return commands

    def _generate_build_commands(self, repo_model: RepoModel) -> Optional[list[str]]:
        """
        Generate build commands if needed.

        Args:
            repo_model: Repository model

        Returns:
            List of build commands or None
        """
        if not repo_model.has_build_step:
            return None

        if not repo_model.build_command:
            return None

        commands = [repo_model.build_command]
        logger.info(f"Build commands: {commands}")
        return commands

    def _generate_docker_specs(self, repo_model: RepoModel) -> Dict:
        """
        Generate docker_specs dictionary.

        Args:
            repo_model: Repository model

        Returns:
            docker_specs dict
        """
        specs = {
            "node_version": repo_model.node_version,
            "_variant": "js_2",  # Use modern JavaScript base image
        }

        # Add pnpm version if using pnpm
        if repo_model.package_manager == "pnpm":
            specs["pnpm_version"] = "9.5.0"  # Default pnpm version

        logger.info(f"Docker specs: {specs}")
        return specs

    def write_constants_file(self, config_model: ConfigModel, output_path: Path) -> None:
        """
        Write the TypeScript constants file.

        Args:
            config_model: Configuration model
            output_path: Path to write the file (e.g., harness/constants/typescript.py)
        """
        # Generate the constants file content
        content = self._generate_constants_file_content(config_model)

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the file
        output_path.write_text(content)
        logger.info(f"Constants file written to: {output_path}")

    def _generate_constants_file_content(self, config_model: ConfigModel) -> str:
        """
        Generate the content for the TypeScript constants file.

        Args:
            config_model: Configuration model

        Returns:
            Python file content as string
        """
        # Convert config to constants entry format
        entry = config_model.to_constants_entry()

        # Format the entry as Python code
        entry_str = self._format_dict_as_python(entry, indent=12)

        # Get repo name for the SPECS dictionary
        repo_name = config_model.repo

        # Generate the file content
        content = f'''"""
Auto-generated TypeScript/JavaScript configuration for SWE-bench.
Generated by ConfigGeneratorAgent.
"""

# Specs for {repo_name}
SPECS_{repo_name.replace("/", "_").replace("-", "_").upper()} = {{
    "{config_model.version}": {entry_str},
}}

# Map repo to version specs
MAP_REPO_VERSION_TO_SPECS_TS = {{
    "{repo_name}": SPECS_{repo_name.replace("/", "_").replace("-", "_").upper()},
}}

# Map repo to install (empty for now)
MAP_REPO_TO_INSTALL_TS = {{}}
'''

        return content

    def _format_dict_as_python(self, d: Dict, indent: int = 0) -> str:
        """
        Format a dictionary as Python code.

        Args:
            d: Dictionary to format
            indent: Current indentation level (spaces)

        Returns:
            Formatted string
        """
        if not d:
            return "{}"

        lines = ["{"]
        indent_str = " " * indent
        item_indent = " " * (indent + 4)

        for key, value in d.items():
            if isinstance(value, dict):
                value_str = self._format_dict_as_python(value, indent + 4)
                lines.append(f'{item_indent}"{key}": {value_str},')
            elif isinstance(value, list):
                if all(isinstance(x, str) for x in value):
                    value_str = "[" + ", ".join(f'"{x}"' for x in value) + "]"
                else:
                    value_str = str(value)
                lines.append(f'{item_indent}"{key}": {value_str},')
            elif isinstance(value, str):
                # Handle multiline strings
                if "\n" in value:
                    value_str = f'"""{value}"""'
                else:
                    value_str = f'"{value}"'
                lines.append(f'{item_indent}"{key}": {value_str},')
            else:
                lines.append(f'{item_indent}"{key}": {value},')

        lines.append(indent_str + "}")
        return "\n".join(lines)
