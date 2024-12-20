from pathlib import Path

from fastapi import FastAPI, Depends
from starlette.responses import RedirectResponse

from modules.configuration_manager import ConfigurationManager
from modules.file_logger import FileLogger
from modules.langchain_embedding_provider import LangchainEmbeddingProvider
from modules.postgres_database_manager import PostgresDatabaseManager
from modules.os_environment_secret_manager import OsEnvironmentSecretManager

from data_processor import DataProcessor

app = FastAPI(title="Data Processor")

configuration_manager = ConfigurationManager()

logger = FileLogger(
    name="data-processor",
    configuration_manager=configuration_manager,
)

secret_manager = OsEnvironmentSecretManager()

embeddings = LangchainEmbeddingProvider(
    logger=logger,
    secret_manager=secret_manager,
    configuration_manager=configuration_manager,
)

database_manager = PostgresDatabaseManager(
    configuration_manager=configuration_manager,
    logger=logger,
    secret_manager=secret_manager,
    embeddings=embeddings,
)

langchain_vector_store = database_manager.create_langchain_vector_store(
    collection_name="test_collection",
)

data_processor = DataProcessor(
    logger=logger,
    secret_manager=secret_manager,
    configuration_manager=configuration_manager,
    data_directory=Path(configuration_manager.get_value("persistent-volume.data_directory")),
    langchain_vector_store=langchain_vector_store,
    chunk_size=3000,
    chunk_overlap=300,
)


@app.get("/")
async def redirect_root():
    return RedirectResponse(url="/docs")

@app.get("/status")
async def read_root() -> dict:
    return {"message": "Data processor is running"}


@app.get("/synchronize-data-directory")
async def synchronize_data_directory() -> dict:
    await data_processor.synchronize_data_directory()
    # return {"message": "Synchronization started in the background."}
    return {"message": "Synchronization not implemented yet"}

def get_data_processor() -> DataProcessor:
    return data_processor

@app.get("/upload_data_from_folder")
async def upload_data_from_folder(data_processor: DataProcessor = Depends(get_data_processor)) -> list:
    try:
        result = await data_processor.upload_data_from_folder()
        return result
    except Exception as e:
        logger.error(f"Failed to upload data from folder: {e}")
        return {"error": "Failed to upload data from folder."}


# for debugging only
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
