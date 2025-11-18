"""
Configuration loader for KATH application.

Loads network configuration from YAML file and environment variables.
Supports runtime configuration updates without container rebuild.

Usage:
    from src.config_loader import load_network_config

    config = load_network_config()
    print(config['backend']['port'])
"""

import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml  # type: ignore


def get_config_file_path() -> Path:
    """
    Get the path to the network configuration file.

    Checks in order:
    1. NETWORK_CONFIG_PATH environment variable
    2. /config/network_config.yaml (Docker/container path)
    3. config/network_config.yaml (relative to project root)
    4. ./network_config.yaml (current directory)

    Returns:
        Path: Path to the configuration file

    Raises:
        FileNotFoundError: If no configuration file is found
    """
    # Check environment variable first
    if env_path := os.getenv("NETWORK_CONFIG_PATH"):
        config_path = Path(env_path)
        if config_path.exists():
            return config_path
        raise FileNotFoundError(f"Config file specified in NETWORK_CONFIG_PATH not found: {env_path}")

    # Check Docker/container path
    container_path = Path("/config/network_config.yaml")
    if container_path.exists():
        return container_path

    # Check relative to project root
    project_path = Path(__file__).parent.parent.parent / "config" / "network_config.yaml"
    if project_path.exists():
        return project_path

    # Check current directory
    current_path = Path("./network_config.yaml")
    if current_path.exists():
        return current_path

    raise FileNotFoundError(
        "network_config.yaml not found in any of the expected locations. "
        "Please create config/network_config.yaml or set NETWORK_CONFIG_PATH environment variable."
    )


def load_network_config() -> Dict[str, Any]:
    """
    Load and parse the network configuration YAML file.

    Returns:
        dict: Configuration dictionary with the following structure:
            {
                'backend': {'host': str, 'port': int, 'domain': str},
                'frontend': {'host': str, 'port': int},
                'cors': {'allowed_origins': str},
                'redis': {'host': str, 'port': int, 'database': int},
                'health_check': {'enabled': bool, 'endpoint': str}
            }

    Raises:
        FileNotFoundError: If configuration file is not found
        yaml.YAMLError: If configuration file is invalid YAML
        KeyError: If required configuration keys are missing
    """
    config_path = get_config_file_path()

    try:
        with open(config_path, "r") as f:
            loaded_config = yaml.safe_load(f)
            config: Dict[str, Any] = loaded_config if loaded_config is not None else {}
    except yaml.YAMLError as e:
        raise yaml.YAMLError(f"Failed to parse YAML configuration from {config_path}: {e}") from e

    return config


def get_backend_config() -> Dict[str, Any]:
    """Get backend configuration from YAML."""
    config = load_network_config()
    backend_config: Dict[str, Any] = config.get("backend", {})
    return backend_config


def get_frontend_config() -> Dict[str, Any]:
    """Get frontend configuration from YAML."""
    config = load_network_config()
    frontend_config: Dict[str, Any] = config.get("frontend", {})
    return frontend_config


def get_cors_config() -> Dict[str, Any]:
    """Get CORS configuration from YAML."""
    config = load_network_config()
    cors_config: Dict[str, Any] = config.get("cors", {})
    return cors_config


def get_redis_config() -> Dict[str, Any]:
    """Get Redis configuration from YAML."""
    config = load_network_config()
    redis_config: Dict[str, Any] = config.get("redis", {})
    return redis_config


def merge_with_environment(yaml_config: Dict[str, Any], env_prefix: str = "") -> Dict[str, Any]:
    """
    Merge YAML configuration with environment variables.

    Environment variables take precedence over YAML values.

    Args:
        yaml_config: Configuration dictionary from YAML file
        env_prefix: Environment variable prefix (e.g., "KATH_")

    Returns:
        dict: Merged configuration with environment variables taking precedence
    """
    merged = yaml_config.copy()

    # Map environment variables to config keys
    env_mapping = {
        "BACKEND_HOST": ("backend", "host"),
        "FLASK_RUN_HOST": ("backend", "host"),
        "BACKEND_PORT": ("backend", "port"),
        "FLASK_RUN_PORT": ("backend", "port"),
        "DOMAIN": ("backend", "domain"),
        "FRONTEND_HOST": ("frontend", "host"),
        "FRONTEND_PORT": ("frontend", "port"),
        "ORIGINS": ("cors", "allowed_origins"),
        "REDIS_HOST": ("redis", "host"),
        "REDIS_PORT": ("redis", "port"),
        "REDIS_DB": ("redis", "database"),
    }

    for env_var, (section, key) in env_mapping.items():
        if env_value := os.getenv(env_var):
            if section not in merged:
                merged[section] = {}
            # Convert to appropriate type
            if key in ["port", "database"]:
                merged[section][key] = int(env_value)
            else:
                merged[section][key] = env_value

    return merged
