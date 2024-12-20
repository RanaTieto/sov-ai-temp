from __future__ import annotations
from typing import TYPE_CHECKING
import os

if TYPE_CHECKING:
    from file_logger import (
        FileLogger,
    )


class OsEnvironmentSecretManager:
    def __init__(self) -> None:
        super().__init__()
        self._logger: FileLogger

    @staticmethod
    def get_secret(secret_name: str) -> str:  # type: ignore
        secret_value = os.getenv(secret_name)
        if secret_value is None:
            error_message = (f"Secret '{secret_name}' "
                             f"not found in environment variables.")
            raise KeyError(error_message)
        return secret_value
