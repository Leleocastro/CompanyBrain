FROM python:3.11-slim AS builder
WORKDIR /app
COPY api/requirements*.txt ./
RUN pip install --user --no-cache-dir -r requirements*.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY api/ .
ENV PATH=/root/.local/bin:$PATH
EXPOSE 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
