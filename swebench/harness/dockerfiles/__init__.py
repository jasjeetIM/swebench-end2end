from __future__ import annotations
from string import Template

# We support Python and JavaScript/TypeScript for SWE-bench.
from . import python as py
from . import javascript as js

def _tmpl(src: str, **kwargs) -> str:
    # Use safe_substitute so $PATH, regex $, etc. aren't mangled.
    return Template(src).safe_substitute(**kwargs)

def _normalize_platform(platform: str | None) -> str:
    if not platform:
        return "linux/x86_64"
    p = platform.strip()
    if p in ("x86_64", "amd64"):
        return "linux/x86_64"
    return p

def get_dockerfile_base(platform, arch, language, **kwargs):
    """
    Generate base Dockerfile for the given language and platform.

    Args:
        platform: e.g., "linux/x86_64"
        arch: e.g., "x86_64" or "arm64"
        language: e.g., "py", "js", "ts"
        **kwargs: Contains ubuntu_version, node_version, _variant, conda_version, etc.

    Returns:
        Dockerfile content as string
    """
    if language == "py":
        # Python implementation
        if arch == "arm64":
            conda_arch = "aarch64"
        else:
            conda_arch = arch

        ubuntu_version = kwargs.get("ubuntu_version", "22.04")
        conda_version = kwargs.get("conda_version", "py311_23.11.0-2")

        return _tmpl(
            py._DOCKERFILE_BASE_PY,
            platform=_normalize_platform(platform),
            conda_arch=conda_arch,
            ubuntu_version=str(ubuntu_version),
            conda_version=str(conda_version),
        )

    elif language in ("js", "ts"):
        # JavaScript/TypeScript implementation
        variant = kwargs.get("_variant", "js_1")
        ubuntu_version = kwargs.get("ubuntu_version", "22.04")

        if variant == "js_2":
            # Modern JS template with direct node installation
            node_version = kwargs.get("node_version", "16")
            return _tmpl(
                js._DOCKERFILE_BASE_JS_2,
                platform=_normalize_platform(platform),
                ubuntu_version=str(ubuntu_version),
                node_version=str(node_version),
            )
        else:
            # Original JS template with NVM
            return _tmpl(
                js._DOCKERFILE_BASE_JS,
                platform=_normalize_platform(platform),
                ubuntu_version=str(ubuntu_version),
            )

    else:
        raise ValueError(f"Unsupported language: {language}")


def get_dockerfile_env(platform, arch, language, base_image_key, **kwargs):
    """
    Generate environment Dockerfile for the given language.

    Args:
        platform: e.g., "linux/x86_64"
        arch: e.g., "x86_64" or "arm64"
        language: e.g., "py", "js", "ts"
        base_image_key: Base image tag to build from
        **kwargs: Contains node_version, python_version, pnpm_version, _variant, etc.

    Returns:
        Dockerfile content as string
    """
    if language == "py":
        # Python environment
        return _tmpl(
            py._DOCKERFILE_ENV_PY,
            platform=_normalize_platform(platform),
            base_image_key=str(base_image_key),
        )

    elif language in ("js", "ts"):
        # JavaScript/TypeScript environment
        variant = kwargs.get("_variant", "js_1")

        if variant == "js_2":
            # For js_2, the env dockerfile is minimal since node is already in base
            return f"""FROM --platform={_normalize_platform(platform)} {base_image_key}

COPY ./setup_env.sh /root/
RUN sed -i -e 's/\\r$//' /root/setup_env.sh
RUN chmod +x /root/setup_env.sh
RUN /bin/bash -c "/root/setup_env.sh"

WORKDIR /testbed/
"""
        else:
            # Original js_1 template with NVM
            node_version = kwargs.get("node_version", "14")
            python_version = kwargs.get("python_version", "3.9")
            pnpm_version = kwargs.get("pnpm_version", "8.6.12")

            return _tmpl(
                js._DOCKERFILE_ENV_JS,
                platform=_normalize_platform(platform),
                base_image_key=str(base_image_key),
                node_version=str(node_version),
                python_version=str(python_version),
                pnpm_version=str(pnpm_version),
            )

    else:
        raise ValueError(f"Unsupported language: {language}")


def get_dockerfile_instance(platform, language, env_image_name):
    """
    Generate instance Dockerfile for the given language.

    Args:
        platform: e.g., "linux/x86_64"
        language: e.g., "py", "js", "ts"
        env_image_name: Environment image tag to build from

    Returns:
        Dockerfile content as string
    """
    if language == "py":
        return _tmpl(
            py._DOCKERFILE_INSTANCE_PY,
            platform=_normalize_platform(platform),
            env_image_name=str(env_image_name),
        )

    elif language in ("js", "ts"):
        return _tmpl(
            js._DOCKERFILE_INSTANCE_JS,
            platform=_normalize_platform(platform),
            env_image_name=str(env_image_name),
        )

    else:
        raise ValueError(f"Unsupported language: {language}")
