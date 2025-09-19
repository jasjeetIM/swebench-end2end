from __future__ import annotations
from string import Template

# We only support 'py' for SWE-bench today.
from . import python as py

def _tmpl(src: str, **kwargs) -> str:
    # Use safe_substitute so $PATH, regex $, etc. aren’t mangled.
    return Template(src).safe_substitute(**kwargs)

def _normalize_platform(platform: str | None) -> str:
    if not platform:
        return "linux/x86_64"
    p = platform.strip()
    if p in ("x86_64", "amd64"):
        return "linux/x86_64"
    return p

def get_dockerfile_base(
    language: str,
    ubuntu_version: str,
    platform: str,
    conda_version: str | None = None,
    **kwargs,
) -> str:
    if language != "py":
        raise ValueError(f"Unsupported language: {language}")
    # conda_version is accepted for forward compatibility but not used by this template.
    return _tmpl(
        py._DOCKERFILE_BASE_PY,
        ubuntu_version=str(ubuntu_version),
        platform=_normalize_platform(platform),
    )

def get_dockerfile_env(
    language: str,
    base_image_key: str,
    platform: str,
    **kwargs,
) -> str:
    if language != "py":
        raise ValueError(f"Unsupported language: {language}")
    return _tmpl(
        py._DOCKERFILE_ENV_PY,
        base_image_key=str(base_image_key),
        platform=_normalize_platform(platform),
    )

def get_dockerfile_instance(
    language: str,
    env_image_name: str,
    platform: str,
    **kwargs,
) -> str:
    if language != "py":
        raise ValueError(f"Unsupported language: {language}")
    return _tmpl(
        py._DOCKERFILE_INSTANCE_PY,
        env_image_name=str(env_image_name),
        platform=_normalize_platform(platform),
    )
