import torch
from pydantic import BaseModel, constr, Field
from sentence_transformers import SentenceTransformer
from fastapi import FastAPI, HTTPException
from starlette.responses import RedirectResponse

from modules.configuration_manager import ConfigurationManager
from modules.file_logger import FileLogger

configuration_manager = ConfigurationManager()

logger = FileLogger(
    name="embeddings",
    configuration_manager=configuration_manager,
)

app = FastAPI(title="Embeddings")

if torch.cuda.is_available():
    device = torch.device("cuda")
elif torch.backends.mps.is_available():
    device = torch.device("mps")
else:
    device = torch.device("cpu")

model = SentenceTransformer(
    model_name_or_path="sentence-transformers/all-mpnet-base-v2",
    device=str(device),
    cache_folder=configuration_manager.get_value("persistent-volume.embeddings_hf_home"),
    # local_files_only=True,
)
model.to(device)


@app.get("/")
async def redirect_root():
    return RedirectResponse(url="/docs")


@app.get("/status")
async def read_root() -> dict:
    return {
        "message": "Embedding API is running",
        "hardware": str(device),
    }


class EmbedDocumentsRequest(BaseModel):
    texts: list[constr(min_length=1, max_length=5120)] = Field(...)


class EmbedDocumentsResponse(BaseModel):
    embeddings: list[list[float]] = None
    error: str = None


@app.post("/embed_documents", response_model=EmbedDocumentsResponse)
async def embed_documents(request: EmbedDocumentsRequest) -> EmbedDocumentsResponse | HTTPException:
    try:
        texts = request.texts
        with torch.no_grad():
            embeddings = [
                model.encode(text, convert_to_tensor=True)
                .to(device)
                .cpu()
                .numpy()
                .tolist()
                for text in texts
            ]
        return EmbedDocumentsResponse(embeddings=embeddings)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class EmbedQueryRequest(BaseModel):
    text: constr(min_length=1, max_length=5120)


class EmbedQueryResponse(BaseModel):
    embedding: list[float] = None
    error: str = None


@app.post("/embed_query", response_model=EmbedQueryResponse)
async def embed_query(request: EmbedQueryRequest) -> EmbedQueryResponse | HTTPException:
    try:
        text = request.text
        with torch.no_grad():
            embedding = (
                model.encode(text, convert_to_tensor=True)
                .to(device)
                .cpu()
                .numpy()
                .tolist()
            )
        return EmbedQueryResponse(embedding=embedding)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# for debugging only
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
