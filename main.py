from ollama import AsyncClient
from ollama._types import ChatRequest, ChatResponse, GenerateRequest, GenerateResponse
from pydantic import BaseModel, ConfigDict
from random import choice
from typing import List, Mapping
from fastapi import FastAPI
from logging import getLogger
from contextlib import asynccontextmanager

logger = getLogger("uvicorn.error")

app = FastAPI()


class ProxyClient(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    host: str
    ollama_client: AsyncClient


class EvalResponse(BaseModel):
    model: str
    host: str
    message: str


class ModelNotFoundError(Exception):
    pass


hosts = ["localhost:8001", "localhost:8002", "localhost:8003", "localhost:8004"]

clients = {
    host: ProxyClient(host=host, ollama_client=AsyncClient(host=host)) for host in hosts
}

supported: Mapping[str, List[AsyncClient]] = {}

async def refresh_model_registry():
    for client in clients.values():
        models = await client.ollama_client.list()
        for model in models.models:
            if model.model not in supported:
                supported[model.model] = [client]
            else:
                supported[model.model].append(client)

async def pick_random_supported_client(model: str) -> ProxyClient:
    if model in supported:
        logger.info(
            f"model {model} supported by hosts {[i.host for i in supported[model]]}"
        )
        return choice(supported[model])
    else:
        await refresh_model_registry()
        if model not in supported:
            raise ModelNotFoundError(
                f"Requested model {model} not found in any configured host"
            )

        logger.info(
            f"model {model} supported by hosts {[i.host for i in supported[model]]}"
        )
        return choice(supported[model])

@asynccontextmanager
async def lifespan(app: FastAPI):
    await refresh_model_registry
    
    yield


@app.post("/api/chat")
async def chat(req: ChatRequest) -> ChatResponse:
    model = req.model
    client = await pick_random_supported_client(model=model)

    logger.info(f"Chose host {client.host} to serve request")
    return await client.ollama_client.chat(**req.model_dump())


@app.post("/api/generate")
async def chat(req: GenerateRequest) -> GenerateResponse:
    model = req.model
    client = await pick_random_supported_client(model=model)

    logger.info(f"Chose host {client.host} to serve request")
    return await client.ollama_client.generate(**req.model_dump())

