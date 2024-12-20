# 1. Builder stage
FROM python:3.12.7-slim AS builder
WORKDIR /data-processor/build
COPY data-processor/requirements.txt .
RUN pip install --default-timeout=600 --no-cache-dir -r requirements.txt

# 2. Final stage
FROM python:3.12.7-slim
WORKDIR /data-processor/src
ENV ENVIRONMENT=development
EXPOSE 8000
COPY data-processor/src /data-processor/src
COPY shared/ /data-processor/src
COPY --from=builder /usr/local /usr/local
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
