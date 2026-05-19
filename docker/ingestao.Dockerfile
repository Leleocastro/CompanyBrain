FROM python:3.11-slim AS builder
WORKDIR /app
COPY ingestao/requirements*.txt ./
RUN pip install --user --no-cache-dir -r requirements*.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY ingestao/ .
ENV PATH=/root/.local/bin:$PATH
CMD ["python", "-m", "ingestao"]
