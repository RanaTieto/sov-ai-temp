import os
from typing import Any
from pathlib import Path

import yaml


class ConfigurationManager:

    def __init__(self) -> None:

        _environment: str | None = os.getenv("ENVIRONMENT")

        try:
            with open("/proc/self/cgroup", "r") as f:
                if _environment == "local":
                    _environment = "local-docker"
        except FileNotFoundError:
            pass

        match _environment:
            case "local":
                file = "../../shared/configuration.local.yaml"
            case "local-docker":
                file = "../../shared/configuration.local.yaml"
            case "development":
                file = "configuration.dev.yaml"
            case "test":
                file = "configuration.test.yaml"
            case "production":
                file = "configuration.prod.yaml"
            case _:
                raise ValueError("ENVIRONMENT variable is not set or invalid.")

        _path: Path = Path(file)
        if not _path.is_file():
            raise FileNotFoundError(f"Configuration file '{file}' not found.")

        try:
            with _path.open("r") as configuration_file:
                self._configuration: dict[str, Any] | list[Any] | None = yaml.safe_load(configuration_file)

                if not isinstance(self._configuration, dict):
                    raise ValueError("Configuration must be a valid dictionary.")

        except yaml.YAMLError as e:
            raise ValueError(f"Error parsing YAML file: {e}")

        except Exception as e:
            raise ValueError(
                f"Unexpected error during "
                f"ConfigurationManager initialization: {e}"
            )

    def get_value(self, keys: str) -> str:

        if not all(char.islower() or char in ["-", "_", "."] for char in keys) or not keys.isascii():
            raise ValueError("The string can only contain lowercase ASCII characters and dots.")

        key_chain: list[str] = keys.split(".")

        current_level = self._configuration

        for key in key_chain:
            if isinstance(current_level, dict) and key in current_level:
                current_level = current_level[key]
            else:
                raise KeyError(f"Key '{key}' not found in the configuration at level: {current_level}")

        return str(current_level)
