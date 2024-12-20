# 1. Builder stage
FROM python:3.12.7-slim AS builder
WORKDIR /backend/build
COPY backend/requirements.txt .
RUN pip install --default-timeout=600 --no-cache-dir -r requirements.txt

# 2. Final stage
FROM python:3.12.7-slim
WORKDIR /backend/src
ENV ENVIRONMENT=development
EXPOSE 8000
COPY backend/src /backend/src
COPY shared/ /backend/src
COPY --from=builder /usr/local /usr/local
CMD [ \
     "uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--timeout-keep-alive", "60", \
     "--workers", "4", \
     "--loop", "uvloop", \
     "--lifespan", "on" \
     ]
