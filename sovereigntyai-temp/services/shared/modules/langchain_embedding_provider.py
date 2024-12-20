from __future__ import annotations
from typing import TYPE_CHECKING

import requests
from langchain_core.embeddings import Embeddings

if TYPE_CHECKING:
    from configuration_manager import ConfigurationManager
    from file_logger import FileLogger
    from os_environment_secret_manager import OsEnvironmentSecretManager


# noinspection DuplicatedCode
class LangchainEmbeddingProvider(Embeddings):

    def __init__(  # noqa: PLR0913
            self,
            logger: FileLogger,
            secret_manager: OsEnvironmentSecretManager,
            configuration_manager: ConfigurationManager,

    ) -> None:
        super().__init__()
        self._logger = logger
        self._configuration_manager = configuration_manager
        self._secret_manager = secret_manager

        self.api_url = configuration_manager.get_value("langchain_embedding_provider.api_url")

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        payload = {"texts": texts}
        response = requests.post(f"{self.api_url}/embed_documents", json=payload)
        response.raise_for_status()
        return response.json()["embeddings"]

    def embed_query(self, text: str) -> list[float]:
        payload = {"text": text}
        response = requests.post(f"{self.api_url}/embed_query", json=payload)
        response.raise_for_status()
        return response.json()["embedding"]
