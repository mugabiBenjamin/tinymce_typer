import json
import os
import tomllib
from pathlib import Path
from typing import Any

from tinymce_typer.config.schema import (
    BOOL_KEYS,
    ENV_KEY_MAP,
    FLOAT_KEYS,
    INT_KEYS,
    LIST_KEYS,
    SUPPORTED_CONFIG_EXTENSIONS,
    is_supported_key,
    normalize_key,
)


class ConfigLoadError(Exception):
    pass


def _parse_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, int):
        return value != 0

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "y", "on"}:
            return True
        if normalized in {"0", "false", "no", "n", "off", ""}:
            return False

    raise ConfigLoadError(f"Invalid boolean value: {value}")


def _coerce_value(key: str, value: Any) -> Any:
    normalized_key = normalize_key(key)

    if value is None:
        return None

    if normalized_key in BOOL_KEYS:
        return _parse_bool(value)

    if normalized_key in INT_KEYS:
        if value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ConfigLoadError(f"Invalid integer for {normalized_key}: {value}") from exc

    if normalized_key in FLOAT_KEYS:
        if value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ConfigLoadError(f"Invalid number for {normalized_key}: {value}") from exc

    if normalized_key in LIST_KEYS:
        if isinstance(value, list):
            return [str(item) for item in value]
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                return []
            return [item.strip() for item in stripped.split(",") if item.strip()]
        raise ConfigLoadError(f"Invalid list for {normalized_key}: {value}")

    return str(value)


def _flatten_config(data: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}

    def walk(prefix: str, value: Any) -> None:
        if isinstance(value, dict):
            for child_key, child_value in value.items():
                next_key = normalize_key(child_key)
                walk(next_key, child_value)
            return

        key = normalize_key(prefix)
        if not is_supported_key(key):
            return

        flattened[key] = _coerce_value(key, value)

    for item_key, item_value in data.items():
        walk(normalize_key(item_key), item_value)

    return flattened


def _load_json(path: Path) -> dict[str, Any]:
    try:
        with path.open("r", encoding="utf-8") as file:
            data = json.load(file)
    except json.JSONDecodeError as exc:
        raise ConfigLoadError(f"Invalid JSON config file: {path}") from exc
    except OSError as exc:
        raise ConfigLoadError(f"Could not read config file: {path}") from exc

    if not isinstance(data, dict):
        raise ConfigLoadError("JSON config must contain an object at the top level.")

    return data


def _load_toml(path: Path) -> dict[str, Any]:
    try:
        with path.open("rb") as file:
            data = tomllib.load(file)
    except tomllib.TOMLDecodeError as exc:
        raise ConfigLoadError(f"Invalid TOML config file: {path}") from exc
    except OSError as exc:
        raise ConfigLoadError(f"Could not read config file: {path}") from exc

    if not isinstance(data, dict):
        raise ConfigLoadError("TOML config must contain a table at the top level.")

    return data


def _load_yaml(path: Path) -> dict[str, Any]:
    try:
        import yaml
    except ImportError as exc:
        raise ConfigLoadError(
            "YAML config files require PyYAML. Use JSON/TOML or install PyYAML."
        ) from exc

    try:
        with path.open("r", encoding="utf-8") as file:
            data = yaml.safe_load(file)
    except yaml.YAMLError as exc:
        raise ConfigLoadError(f"Invalid YAML config file: {path}") from exc
    except OSError as exc:
        raise ConfigLoadError(f"Could not read config file: {path}") from exc

    if data is None:
        return {}

    if not isinstance(data, dict):
        raise ConfigLoadError("YAML config must contain a mapping at the top level.")

    return data


def _load_file_config(path: Path) -> dict[str, Any]:
    resolved = path.expanduser()

    if not resolved.exists():
        raise ConfigLoadError(f"Config file does not exist: {resolved}")

    if not resolved.is_file():
        raise ConfigLoadError(f"Config path is not a file: {resolved}")

    suffix = resolved.suffix.lower()

    if suffix not in SUPPORTED_CONFIG_EXTENSIONS:
        allowed = ", ".join(sorted(SUPPORTED_CONFIG_EXTENSIONS))
        raise ConfigLoadError(f"Unsupported config file extension '{suffix}'. Allowed: {allowed}")

    if suffix == ".json":
        return _flatten_config(_load_json(resolved))

    if suffix == ".toml":
        return _flatten_config(_load_toml(resolved))

    if suffix in {".yaml", ".yml"}:
        return _flatten_config(_load_yaml(resolved))

    raise ConfigLoadError(f"Unsupported config file extension: {suffix}")


def _load_env_config() -> dict[str, Any]:
    config: dict[str, Any] = {}

    for env_key, config_key in ENV_KEY_MAP.items():
        if env_key not in os.environ:
            continue

        raw_value = os.environ[env_key]
        if raw_value == "":
            continue

        config[config_key] = _coerce_value(config_key, raw_value)

    return config


def load_config(path: Path | None = None) -> dict[str, Any]:
    env_config = _load_env_config()

    if path is None:
        return env_config

    file_config = _load_file_config(path)

    merged = dict(env_config)
    merged.update(file_config)
    merged["config_path"] = str(path)

    return merged