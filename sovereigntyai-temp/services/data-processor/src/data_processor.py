from __future__ import annotations

import glob
import os
from typing import TYPE_CHECKING
import hashlib
import logging
import mimetypes
from datetime import datetime, timezone
from pathlib import Path

import langdetect
from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langdetect import detect
from sqlalchemy import create_engine, Table, Column, String, MetaData

if TYPE_CHECKING:
    from langchain_postgres.vectorstores import PGVector

    from modules.configuration_manager import ConfigurationManager
    from modules.file_logger import FileLogger
    from modules.os_environment_secret_manager import OsEnvironmentSecretManager


class DataProcessor:

    def __init__(  # noqa: PLR0913
            self,
            logger: FileLogger,
            secret_manager: OsEnvironmentSecretManager,
            configuration_manager: ConfigurationManager,
            data_directory: Path,
            langchain_vector_store: PGVector,
            chunk_size: int,
            chunk_overlap: int,
    ) -> None:
        self._logger = logger
        self._configuration_manager = configuration_manager
        self._secret_manager = secret_manager
        self._DATA_DIRECTORY = data_directory
        self._LANGCHAIN_VECTOR_STORE = langchain_vector_store
        self._SUPPORTED_MIME_TYPES = ("text/plain",)
        self._TEXT_SPLITTER = RecursiveCharacterTextSplitter(
            # separators=[
            #     ".\n\n",
            #     ".\r\n\r\n",
            #     "\n\n",
            #     "\r\n\r\n",
            #     # optional
            #     ".\n",
            #     ".\r\n",
            # ],
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
            is_separator_regex=False,
        )

    # class File:
    #     def __init__(
    #             self,
    #             path: str,
    #             name: str,
    #             mime_type: str | None,
    #             hash_value: str,
    #     ) -> None:
    #         self.path = path
    #         self.name = name
    #         self.mime_type = mime_type
    #         self.hash = hash_value
    #
    # @staticmethod
    # def _detect_file_type(file_path: Path) -> str | None:
    #     mime_type, _ = mimetypes.guess_type(file_path)
    #     return mime_type
    #
    # def _detect_file_language(self, file_path: str) -> str | None:
    #     try:
    #         with Path.open(Path(file_path), encoding="utf-8") as file:
    #             file_content = file.read()
    #             return langdetect.detect(file_content)
    #     except (
    #             FileNotFoundError,
    #             Exception,
    #             langdetect.lang_detect_exception.LangDetectException,
    #     ) as e:
    #         self._logger.info(f"Error occurred: {file_path}. Error: {e}")
    #         return None
    #
    # def _create_file_list(self) -> list[File]:
    #     all_files_and_dirs = sorted(self._DATA_DIRECTORY.rglob("*"))
    #     all_files = [
    #         file for file in all_files_and_dirs
    #         if file.is_file() and self._detect_file_type(file) in
    #            self._SUPPORTED_MIME_TYPES
    #     ]
    #     return [
    #         self.File(
    #             file_path.as_posix(),
    #             file_path.name,
    #             self._detect_file_type(file_path),
    #             hashlib.sha256(
    #                 file_path.read_bytes(),
    #             ).hexdigest(),
    #         )
    #         for file_path in all_files
    #     ]
    #
    # def _create_record_metadata_set(self) -> set[str]:
    #     all_records = self._LANGCHAIN_VECTOR_STORE.get()
    #     # all_records = self._LANGCHAIN_VECTOR_STORE.similarity_search("")
    #
    #     query = f"SELECT * FROM {self._LANGCHAIN_VECTOR_STORE.collection_name}"
    #     all_records = self._LANGCHAIN_VECTOR_STORE.session.execute(query).fetchall()
    #
    #     record_metadata_set = set()
    #
    #     if not all_records:
    #         return record_metadata_set
    #
    #     for record in all_records["metadatas"]:
    #         file_path = record["file_path"]
    #         if file_path:
    #             record_metadata_set.add(file_path)
    #     return record_metadata_set
    #
    # def _load_text_file(self, file: File) -> None:
    #
    #     source_file_name = None
    #     try:
    #         with open(file.path, "r", encoding="utf-8") as f:
    #             source_file_name = f.readline().strip()
    #     except Exception as e:
    #         print(f"Error reading file: {e}")
    #
    #     loader = TextLoader(file.path, encoding="utf-8")
    #
    #     documents = loader.load_and_split()
    #
    #     if documents:
    #         meta_data = {
    #             "source_file_name": source_file_name,
    #             "file_name": file.name,
    #             "file_path": file.path,
    #             "file_directory": Path(file.path).parts[1]
    #             if len(Path(file.path).parts) > 1 else None,
    #             "file_hash": file.hash,
    #             "language": self._detect_file_language(file.path),
    #         }
    #
    #         for document in documents:
    #             document.metadata = meta_data
    #
    #         chunks = self._TEXT_SPLITTER.split_documents(documents)
    #
    #         self._LANGCHAIN_VECTOR_STORE.add_documents(
    #             documents=chunks,
    #         )
    #
    # def _delete_records_by_metadata(
    #         self,
    #         file_path: str | None,
    #         file_hash: str | None = None,
    # ) -> None:
    #
    #     records_to_delete = None
    #
    #     if file_path and file_hash:
    #         result = self._LANGCHAIN_VECTOR_STORE.get(
    #             where={
    #                 "$and": [
    #                     {"file_path": {"$eq": file_path}},
    #                     {"file_hash": {"$ne": file_hash}},
    #                 ],
    #             },
    #         )
    #         records_to_delete = result["ids"]
    #
    #     if file_path and not file_hash:
    #         result = self._LANGCHAIN_VECTOR_STORE.get(
    #             where={"file_path": file_path},
    #         )
    #         records_to_delete = result["ids"]
    #
    #     if records_to_delete:
    #         self._LANGCHAIN_VECTOR_STORE.delete(ids=records_to_delete)
    #         message = f"Records for file: {file_path} have been deleted"
    #     else:
    #         message = (f"No invalid records found for deletion for file: "
    #                    f"{file_path}")
    #
    #     self._logger.info(message)
    #
    # def _get_record_count_by_metadata(self, file: File) -> int:
    #     result = self._LANGCHAIN_VECTOR_STORE.get(
    #         where={
    #             "$and": [
    #                 {"file_path": {"$eq": file.path}},
    #                 {"file_hash": {"$eq": file.hash}},
    #             ],
    #         },
    #     )
    #     return len(result["ids"])
    #
    # logging.basicConfig(
    #     level=logging.INFO,
    #     format="%(asctime)s - %(levelname)s - %(message)s",
    # )
    #
    # async def synchronize_data_directory(self) -> str:
    #     time_zone = timezone.utc
    #     start_time = datetime.now(tz=time_zone)
    #     logging.info(
    #         f"Started at: "  # noqa: G004
    #         f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
    #     )
    #
    #     try:
    #         file_list = self._create_file_list()
    #         # record_metadata_set = self._create_record_metadata_set()
    #     except Exception as e:
    #         logging.exception(
    #             f"Error creating file list or metadata set: "  # noqa: G004
    #             f"{e}")  # noqa: TRY401
    #         return "Error during initialization"
    #
    #     # delete records of nonexistent files
    #
    #     # for path in record_metadata_set:
    #     #     try:
    #     #         file_exists = any(file.path == path for file in file_list)
    #     #         if not file_exists:
    #     #             self._delete_records_by_metadata(path)
    #     #     except Exception as e:
    #     #         logging.exception(
    #     #             f"Error deleting records for path "  # noqa: G004
    #     #             f"{path}: {e}",  # noqa: TRY401
    #     #         )
    #
    #     total_files = len(file_list)
    #
    #     for i, file in enumerate(file_list):
    #         file_start_time = datetime.now(tz=time_zone)
    #         logging.info(
    #             f"Processing {file.name}... (started at "  # noqa: G004
    #             f"{file_start_time.strftime('%Y-%m-%d %H:%M:%S')} "
    #             f"UTC)",
    #         )
    #
    #         try:
    #             # delete records of files with changed content/hash
    #             # self._delete_records_by_metadata(file.path, file.hash)
    #
    #             # check for records with metadata file_path and file_hash
    #             # record_count = self._get_record_count_by_metadata(file)
    #
    #             # TODO(Pavel): fix synchronization
    #             # temporarily solution
    #
    #             # insert file if it is missing
    #             record_count = 0
    #             if record_count == 0:  # noqa: SIM102
    #                 if file.mime_type == "text/plain":
    #                     self._load_text_file(file)
    #
    #             file_end_time = datetime.now(tz=time_zone)
    #             file_duration = ((file_end_time - file_start_time)
    #                              .total_seconds())
    #             progress_percentage = ((i + 1) / total_files) * 100
    #             logging.info(
    #                 f"\rProcessed {file.name}, "  # noqa: G004
    #                 f"{file_duration:.2f} seconds, {i + 1}/"
    #                 f"{total_files}, "
    #                 f"{progress_percentage:.2f}% done")
    #
    #         except Exception as e:
    #             logging.exception(
    #                 f"Error processing file "  # noqa: G004
    #                 f"{file.name}: {e}",  # noqa: TRY401
    #             )
    #
    #     end_time = datetime.now(tz=time_zone)
    #     duration = end_time - start_time
    #     logging.info(
    #         f"Finished at: "  # noqa: G004
    #         f"{end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
    #     )
    #     logging.info(f"Total duration: {duration}")  # noqa: G004
    #
    #     return "Synchronization complete"

    @staticmethod
    def _calculate_file_hash(file_path):
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    @staticmethod
    def _detect_language(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
        try:
            return detect(file_content)
        except Exception as e:
            return "unknown"

    @staticmethod
    def _read_file_content(file_path):
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()

    async def upload_data_from_folder(self) -> list:
        time_zone = timezone.utc
        start_time = datetime.now(tz=time_zone)
        logging.info(
            f"Started at: "  # noqa: G004
            f"{start_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
        )

        directory = self._configuration_manager.get_value("persistent-volume.data_directory")
        files = glob.glob(f"{directory}/**/*.txt", recursive=True)

        print(files)

        file_list = [
            (
                os.path.relpath(os.path.dirname(file), directory),
                os.path.basename(file),
                self._calculate_file_hash(file),
                self._detect_language(file),
                self._read_file_content(file)
            ) for file in files
        ]


        engine = create_engine(self._configuration_manager.get_value("database.connection_string"))
        metadata = MetaData()

        # Assuming a metadata table with file_path, file_name, and file_hash
        files_metadata_table = Table(
            "files_metadata", metadata,
            Column("file_path", String, primary_key=True),
            Column("file_name", String),
            Column("file_hash", String),
            Column("language", String)
        )

        with engine.connect() as connection:
            for file_path, file_name, file_hash, language, file_content in file_list:
                result = connection.execute(
                    files_metadata_table.select().where(files_metadata_table.c.file_hash == file_hash)
                ).fetchone()

                if result:
                    self._logger.info(f"File {file_name} already processed. Skipping.")
                    continue

                # If not processed, insert metadata and optionally process further
                connection.execute(
                    files_metadata_table.insert().values(
                        file_path=file_path,
                        file_name=file_name,
                        file_hash=file_hash,
                        language=language
                    )
                )

                # Optional: Process file content (e.g., store chunks in the vector store)
                chunks = self._TEXT_SPLITTER.split_text(file_content)
                for chunk in chunks:
                    self._LANGCHAIN_VECTOR_STORE.add_texts([chunk])
                    self._logger.info(f"Added chunk for file {file_name}.")


                end_time = datetime.now(tz=time_zone)
                duration = end_time - start_time
                logging.info(
                    f"Finished at: "  # noqa: G004
                    f"{end_time.strftime('%Y-%m-%d %H:%M:%S')} UTC",
                )
                logging.info(f"Total duration: {duration}")  # noqa: G004

                # return "Synchronization complete"
                return file_list
