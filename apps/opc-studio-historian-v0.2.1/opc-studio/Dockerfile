FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV OPC_STUDIO_HTTP_PORT=8040
ENV OPC_UA_PORT=4840
ENV OPC_ENDPOINT=opc.tcp://0.0.0.0:4840/shopfloor/opc-studio
ENV DATABASE_URL=postgresql://postgres:postgres@postgres:5432/ragdb
ENV HISTORIAN_ENABLED=true
ENV HISTORIAN_INTERVAL_S=5
ENV LOG_LEVEL=info

CMD ["python", "-m", "app.main"]
