FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app
COPY main.py requirements.txt /app/

RUN uv pip install -r requirements.txt --system

ENTRYPOINT [ "fastapi" ]
CMD ["run", "--host", "0.0.0.0", "--port", "11434"]