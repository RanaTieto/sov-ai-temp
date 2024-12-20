import os
import sys
import io

from fastapi import FastAPI
from pydantic import BaseModel, constr
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from modules.configuration_manager import ConfigurationManager
from modules.os_environment_secret_manager import OsEnvironmentSecretManager
from modules.file_logger import FileLogger
from modules.postgres_database_manager import PostgresDatabaseManager
from modules.langchain_llm_client import LangchainLlmClient
from modules.langchain_embedding_provider import LangchainEmbeddingProvider

# Set output to UTF-8 for proper text handling
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

# Configuration Manager
configuration_manager = ConfigurationManager()
# os.environ["HF_HOME"] = configuration_manager.get_value("persistent-volume.hf_home")

# Secret Manager
secret_manager = OsEnvironmentSecretManager()

# Logger
logger = FileLogger(
    name="backend",
    configuration_manager=configuration_manager,
)

# Embeddings
embeddings = LangchainEmbeddingProvider(
    logger=logger,
    secret_manager=secret_manager,
    configuration_manager=configuration_manager,
)

# Database Manager
database_manager = PostgresDatabaseManager(
    logger=logger,
    secret_manager=secret_manager,
    configuration_manager=configuration_manager,
    embeddings=embeddings,
)

# Vector Store
langchain_vector_store = database_manager.create_langchain_vector_store(
    collection_name="test_collection",
)

# LLM Client
llm_client = LangchainLlmClient(
    logger=logger,
    secret_manager=secret_manager,
    configuration_manager=configuration_manager,
    model="llama3.2:1b-instruct-q2_K",
    temperature=0,
    max_tokens=2048,
    langchain_vector_store=langchain_vector_store,
    collection_name="test",
)

# Create an instance of FastAPI
app = FastAPI(title="Backend")

# Set CORS middleware
# noinspection PyTypeChecker
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def redirect_to_docs():
    return RedirectResponse(url="/docs")


class QuestionRequest(BaseModel):
    question: constr(min_length=1, max_length=5120)


class QuestionResponse(BaseModel):
    answer: str
    feedback_id: str


@app.post("/question", response_model=QuestionResponse)
async def get_answer(request: QuestionRequest) -> QuestionResponse:
    question = request.question
    answer, feedback_id = llm_client.ask_database(
        5,
        0.2,
        question,
    )
    return QuestionResponse(answer=answer, feedback_id=feedback_id)


class FeedbackRequest(BaseModel):
    feedback_id: str
    value: constr(min_length=1, max_length=5120)


class FeedbackResponse(BaseModel):
    answer: str
    feedback_id: str


@app.post("/feedback", response_model=FeedbackResponse)
async def submit_feedback(request: FeedbackRequest) -> FeedbackResponse:
    feedback_id = request.feedback_id
    value = request.value
    return FeedbackResponse(answer=value, feedback_id=feedback_id)


# for debugging only
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
