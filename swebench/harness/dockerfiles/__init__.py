from __future__ import annotations
from string import Template


def _tmpl(src: str, **kwargs) -> str:
    # Safe formatter: ignores $... that we didn't pass (e.g., $PATH, sed's $ anchor)
    return Template(src).safe_substitute(**kwargs)


def _normalize_platform(p: str | None) -> str:
    if not p:
        return "linux/x86_64"
    p = p.strip()
    if p in ("x86_64", "amd64"):
        return "linux/x86_64"
    return p


def _coerce_args_for_base(language: str, args: tuple, kwargs: dict) -> tuple[str, dict]:
    """
    Accepts legacy/incorrect positional ordering and normalizes:
      expected keys: language='py', ubuntu_version, platform
      frequent bad call: get_dockerfile_base("linux/x86_64", ubuntu_version="22.04")
    """
    # If first positional looks like a platform, it was passed as "language".
    if isinstance(language, str) and "/" in language:
        # Move this into platform, and default language to 'py' (the only supported one)
        kwargs.setdefault("platform", language)
        language = kwargs.pop("language", "py")

    # Map remaining positionals if any
    if len(args) >= 1 and "ubuntu_version" not in kwargs:
        kwargs["ubuntu_version"] = args[0]
    if len(args) >= 2 and "platform" not in kwargs:
        kwargs["platform"] = args[1]

    # Defaults
    kwargs.setdefault("ubuntu_version", "22.04")
    kwargs["platform"] = _normalize_platform(kwargs.get("platform"))
    return language, kwargs


def _coerce_args_for_env(language: str, args: tuple, kwargs: dict) -> tuple[str, dict]:
    """
    expected keys: language='py', base_image_key, platform
    tolerate legacy orders like:
      get_dockerfile_env("py", base_image_key, "linux/x86_64")
      get_dockerfile_env("py", "linux/x86_64", base_image_key)
      get_dockerfile_env("linux/x86_64", base_image_key)  # language omitted/shifted
    """
    # If first positional looks like a platform, it was passed as "language".
    if isinstance(language, str) and "/" in language:
        kwargs.setdefault("platform", language)
        language = kwargs.pop("language", "py")

    # If caller already used kwargs, prefer them
    base_kw = kwargs.get("base_image_key")
    plat_kw = kwargs.get("platform")

    # Heuristics to identify args regardless of order
    platform_candidates = set()
    base_candidates = set()

    def looks_like_platform(s: str) -> bool:
        s = s.strip()
        return (s.startswith("linux/") or s in {"x86_64", "amd64", "linux/amd64", "linux/x86_64"})

    def looks_like_base_image(s: str) -> bool:
        # We expect something like "sweb.base.py.x86_64:latest"
        # or any repo:tag form containing ":" (but avoid windows paths)
        return (":" in s) or ("sweb.base" in s) or (s.startswith("sweb.base."))

    for a in args:
        if isinstance(a, str):
            if looks_like_platform(a):
                platform_candidates.add(a)
            if looks_like_base_image(a):
                base_candidates.add(a)

    # Assign from kwargs first, then heuristics, then positional fallback
    if not base_kw:
        if base_candidates:
            kwargs["base_image_key"] = next(iter(base_candidates))
        elif len(args) >= 1:
            kwargs.setdefault("base_image_key", args[0])

    if not plat_kw:
        if platform_candidates:
            kwargs["platform"] = next(iter(platform_candidates))
        elif len(args) >= 2:
            kwargs.setdefault("platform", args[1])

    if not kwargs.get("base_image_key"):
        raise ValueError("base_image_key is required")

    # Normalize/validate platform
    kwargs["platform"] = _normalize_platform(kwargs.get("platform"))
    if kwargs["platform"] not in {"linux/x86_64", "linux/amd64"}:
        # If something bizarre slipped in (e.g., a tag), default to sane platform
        kwargs["platform"] = "linux/x86_64"

    return language or "py", kwargs



def _coerce_args_for_instance(language: str, args: tuple, kwargs: dict) -> tuple[str, dict]:
    """
    expected keys: language='py', env_image_name, platform
    legacy positional: get_dockerfile_instance("py", env_image_name, "linux/x86_64")
    bad call we tolerate: get_dockerfile_instance("linux/x86_64", env_image_name)
    """
    if isinstance(language, str) and "/" in language:
        kwargs.setdefault("platform", language)
        language = kwargs.pop("language", "py")

    if len(args) >= 1 and "env_image_name" not in kwargs:
        kwargs["env_image_name"] = args[0]
    if len(args) >= 2 and "platform" not in kwargs:
        kwargs["platform"] = args[1]

    if not kwargs.get("env_image_name"):
        raise ValueError("env_image_name is required")

    kwargs["platform"] = _normalize_platform(kwargs.get("platform"))
    return language, kwargs


def get_dockerfile_base(language: str, *args, **kwargs) -> str:
    from .python import _DOCKERFILE_BASE_PY
    language, kwargs = _coerce_args_for_base(language, args, kwargs)
    if language != "py":
        # Only 'py' is supported today; normalize any weird inputs to py if caller provided it in kwargs
        if kwargs.get("language") == "py":
            language = "py"
        else:
            raise ValueError(f"Unsupported language: {language}")
    return _tmpl(_DOCKERFILE_BASE_PY, **kwargs)


def get_dockerfile_env(language: str, *args, **kwargs) -> str:
    from .python import _DOCKERFILE_ENV_PY
    language, kwargs = _coerce_args_for_env(language, args, kwargs)
    if language != "py":
        if kwargs.get("language") == "py":
            language = "py"
        else:
            raise ValueError(f"Unsupported language: {language}")
    return _tmpl(_DOCKERFILE_ENV_PY, **kwargs)


def get_dockerfile_instance(language: str, *args, **kwargs) -> str:
    from .python import _DOCKERFILE_INSTANCE_PY
    language, kwargs = _coerce_args_for_instance(language, args, kwargs)
    if language != "py":
        if kwargs.get("language") == "py":
            language = "py"
        else:
            raise ValueError(f"Unsupported language: {language}")
    return _tmpl(_DOCKERFILE_INSTANCE_PY, **kwargs)
