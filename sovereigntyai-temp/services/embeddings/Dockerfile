# 1. Builder stage
FROM python:3.12.7-slim AS builder
WORKDIR /embeddings/build
COPY embeddings/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 2. Final stage
FROM python:3.12.7-slim
WORKDIR /embeddings/src
ENV HF_HOME=/embeddings_data
EXPOSE 8000
COPY embeddings/src /embeddings/src
COPY shared/ /embeddings/src
COPY --from=builder /usr/local /usr/local
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
