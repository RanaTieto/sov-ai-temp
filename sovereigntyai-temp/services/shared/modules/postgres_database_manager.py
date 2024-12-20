from __future__ import annotations
from typing import TYPE_CHECKING

from langchain_core.embeddings import Embeddings
from langchain_postgres.vectorstores import PGVector

if TYPE_CHECKING:
    from configuration_manager import ConfigurationManager
    from file_logger import FileLogger
    from os_environment_secret_manager import OsEnvironmentSecretManager


# noinspection DuplicatedCode
class PostgresDatabaseManager:

    def __init__(
            self,
            configuration_manager: ConfigurationManager,
            logger: FileLogger,
            secret_manager: OsEnvironmentSecretManager,
            embeddings: Embeddings
    ) -> None:
        super().__init__()
        self._configuration_manager = configuration_manager
        self._logger = logger
        self._secret_manager = secret_manager
        self._embeddings = embeddings

    def create_langchain_vector_store(self, collection_name: str) -> PGVector:
        host = self._configuration_manager.get_value("postgres_database_manager.host")
        port = self._configuration_manager.get_value("postgres_database_manager.port")
        database_name = self._configuration_manager.get_value("postgres_database_manager.database_name")
        user = self._configuration_manager.get_value("postgres_database_manager.user")
        password = self._secret_manager.get_secret("DB_PASSWORD")

        connection = f"postgresql+psycopg://{user}:{password}@{host}:{port}/{database_name}"

        return PGVector(
            embeddings=self._embeddings,
            connection=connection,
            collection_name=collection_name,
            use_jsonb=True,
        )
