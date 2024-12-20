import logging
import os
import sys
from datetime import datetime, timezone
from logging.handlers import RotatingFileHandler
from pathlib import Path
import socket

from modules.configuration_manager import ConfigurationManager


class CustomFormatter(logging.Formatter):
    def __init__(  # type: ignore
            self,
            *args,  # noqa: ANN002
            hostname: str = "",
            environment: str = "",
            job_id: str = "",
            **kwargs,  # noqa: ANN003
    ) -> None:
        super().__init__(
            *args,
            **kwargs,
        )
        self.hostname = hostname
        self.environment = environment
        self.job_id = job_id

        # TODO(Pavel): add methods info etc... and fix it also in backend and other modules

    def set_job_id(self, job_id: str) -> None:
        self.job_id = job_id

    def format(self, record: logging.LogRecord) -> str:  # noqa: A003
        record.hostname = self.hostname
        record.environment = self.environment
        record.job_id = self.job_id
        return super().format(record)


# noinspection DuplicatedCode
class FileLogger:

    def __init__(
            self,
            name: str,
            configuration_manager: ConfigurationManager,
    ) -> None:
        self._name = name
        self._level = configuration_manager.get_value("file_logger.level")
        self._directory = configuration_manager.get_value("persistent-volume.logging")
        self._initialize_logger()

    def set_job_id(self, job_id: str) -> None:
        self._formatter.set_job_id(job_id)

    @staticmethod
    def _get_logging_level(level_str: str) -> int:
        level_str = level_str.upper()
        level = logging.getLevelName(level_str)
        if isinstance(level, int) and level in {
            logging.DEBUG,
            logging.INFO,
            logging.WARNING,
            logging.ERROR,
            logging.CRITICAL,
        }:
            return level
        error_message = f"Invalid logging level: {level_str}"
        raise ValueError(error_message)

    def _initialize_logger(self) -> logging.Logger:
        self.logger = logging.getLogger(self._name)
        self.logger.setLevel(
            self._get_logging_level(self._level),
        )  # type: ignore
        _directory_path = Path(self._directory)
        _directory_path.mkdir(parents=True, exist_ok=True)
        _file = (f"{_directory_path}/"
                 f"{self._name}_{datetime.now(timezone.utc).strftime('%Y-%m-%d')}.csv")
        _file_path = Path(_file)

        if (not Path.exists(_file_path) or
                _file_path.stat().st_size == 0):
            with _file_path.open("a") as f:
                f.write("Timestamp;Hostname;Environment;Level;Logger;JobId;Path;LineNo;ProcessID;Message;Traceback;\n")

        _logging_handler = RotatingFileHandler(
            _file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )

        _console_handler = logging.StreamHandler(sys.stdout)

        self._formatter = CustomFormatter(
            "%(asctime)s;"
            "%(hostname)s;"
            "%(environment)s;"
            "%(levelname)s;"
            "%(name)s;"
            "%(job_id)s;"
            "%(pathname)s;"
            "%(lineno)d;"
            "%(process)d;"
            "%(message)s",
            hostname=socket.gethostname(),
            environment=os.getenv("ENVIRONMENT", ""),
            job_id="",
        )

        _logging_handler.setFormatter(self._formatter)
        _console_handler.setFormatter(self._formatter)
        self.logger.addHandler(_logging_handler)
        self.logger.addHandler(_console_handler)

        return self.logger
