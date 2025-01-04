from ollama import Client
from ollama._types import ChatRequest, ChatResponse, GenerateRequest, GenerateResponse
from pydantic import BaseModel, ConfigDict
from random import choice
from typing import Set, Mapping, Union, Iterator, Generator
from types import GeneratorType
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse, StreamingResponse, JSONResponse
from logging import getLogger
from contextlib import asynccontextmanager

logger = getLogger("uvicorn.error")

app = FastAPI()


class ProxyClient(BaseModel, frozen=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    host: str
    ollama_client: Client


class EvalResponse(BaseModel):
    model: str
    host: str
    message: str


class ModelNotFoundError(Exception):
    pass


hosts = ["ollama0:11434"]

clients = {
    host: ProxyClient(host=host, ollama_client=Client(host=host)) for host in hosts
}

supported: Mapping[str, Set[Client]] = {}


async def refresh_model_registry():
    for client in clients.values():
        models = client.ollama_client.list()
        for model in models.models:
            if model.model not in supported:
                supported[model.model] = set([client])
            else:
                supported[model.model].add(client)


async def pick_random_supported_client(model: str) -> ProxyClient:
    if model in supported:
        logger.info(
            f"model {model} supported by hosts {[i.host for i in supported[model]]}"
        )
        return choice(list(supported[model]))
    else:
        await refresh_model_registry()
        if model not in supported:
            raise ModelNotFoundError(
                f"Requested model {model} not found in any configured host"
            )

        logger.info(
            f"model {model} supported by hosts {[i.host for i in supported[model]]}"
        )
        return choice(list(supported[model]))


@asynccontextmanager
async def lifespan(app: FastAPI):
    await refresh_model_registry()

    yield


@app.post("/api/chat")
async def chat(req: ChatRequest):
    model = req.model
    stream = req.stream
    client = await pick_random_supported_client(model=model)

    logger.info(f"Chose host {client.host} to serve request")
    resp: Union[ChatResponse, Iterator[ChatResponse]] = client.ollama_client.chat(**req.model_dump())

    async def streamer(iter: Iterator[ChatResponse]):
        for i in iter:
            yield i.model_dump_json()
    
    if stream:
        return StreamingResponse(content=streamer(resp))
    else:
        return JSONResponse(content=resp.model_dump_json())


@app.post("/api/generate")
async def generate(
    req: GenerateRequest,
):
    model = req.model
    stream = req.stream
    client = await pick_random_supported_client(model=model)

    logger.info(f"Chose host {client.host} to serve request")
    resp: Union[GenerateResponse, Iterator[GenerateResponse]] = (
        client.ollama_client.generate(**req.model_dump())
    )

    async def streamer(iter: Iterator[GenerateResponse]):
        for i in iter:
            yield i.model_dump_json()
        

    if stream:
        return StreamingResponse(content=streamer(resp))
    else:
        return JSONResponse(content=resp.model_dump_json())


@app.get("/models")
async def models():
    await refresh_model_registry()
    return {model: [i.host for i in clients] for model, clients in supported.items()}


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "Ollama is running"
