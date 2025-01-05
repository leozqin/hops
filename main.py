from ollama import Client as OllamaClient
from ollama._types import (
    ChatRequest,
    ChatResponse,
    GenerateRequest,
    GenerateResponse,
    ModelDetails,
    EmbedRequest,
    EmbedResponse,
    ShowRequest,
    ShowResponse,
)
from pydantic import BaseModel, ConfigDict
from random import choice
from typing import Set, Mapping, Union, Iterator, List, Sequence, Optional
from datetime import datetime
from types import GeneratorType
from fastapi import FastAPI, HTTPException
from fastapi.responses import PlainTextResponse, StreamingResponse, JSONResponse
from logging import getLogger
from contextlib import asynccontextmanager

logger = getLogger("uvicorn.error")


class ListModel(BaseModel, frozen=True):
    name: str
    model: str
    modified_at: Optional[datetime] = None
    digest: Optional[str] = None
    size: Optional[int] = None
    details: Optional[ModelDetails] = None


class CustomListResponse(BaseModel):
    models: Sequence[ListModel]


class ProxyClient(BaseModel, frozen=True):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    host: str
    ollama_client: OllamaClient
    models: Sequence[ListModel]


class EvalResponse(BaseModel):
    model: str
    host: str
    message: str


class ModelNotFoundError(Exception):

    def __init__(self, model: str):
        self.model = model

    @property
    def message(self):
        return f"model {self.model} was not found in any configured host"


hosts = ["ollama0:11434"]
clients: Mapping[str, ProxyClient] = {}
supported: Mapping[str, List[ProxyClient]] = {}


async def discover_hosts():
    for host in hosts:
        host_client = OllamaClient(host=host)
        models = host_client.list()

        list_models = [ListModel(name=i.model, **i.model_dump()) for i in models.models]

        proxy_client = ProxyClient(
            host=host, ollama_client=host_client, models=list_models
        )

        clients.update({host: proxy_client})


async def refresh_model_registry():
    for client in clients.values():
        for model in client.models:
            if model.model not in supported:
                supported[model.model] = [client]
            elif client.host not in [i.host for i in supported[model.model]]:
                supported[model.model].append(client)


async def pick_random_supported_client(model: str) -> OllamaClient:
    if model not in supported:
        await refresh_model_registry()
        if model not in supported:
            raise ModelNotFoundError(model=model)
    else:
        logger.info(
            f"model {model} supported by hosts {[i.host for i in supported[model]]}"
        )
        client = choice(supported[model])

        return client.ollama_client


# Routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    await discover_hosts()
    await refresh_model_registry()

    yield


app = FastAPI(lifespan=lifespan)


@app.post("/api/chat")
async def chat(req: ChatRequest):
    model = req.model
    stream = req.stream
    try:
        client = await pick_random_supported_client(model=model)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

    resp: Union[ChatResponse, Iterator[ChatResponse]] = client.chat(**req.model_dump())

    async def streamer(iter: Iterator[ChatResponse]):
        for i in iter:
            yield i.model_dump_json()

    if stream:
        return StreamingResponse(content=streamer(resp))
    else:
        return JSONResponse(content=resp.model_dump())


@app.post("/api/generate")
async def generate(
    req: GenerateRequest,
):
    model = req.model
    stream = req.stream
    try:
        client = await pick_random_supported_client(model=model)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

    resp: Union[GenerateResponse, Iterator[GenerateResponse]] = client.generate(
        **req.model_dump()
    )

    async def streamer(iter: Iterator[GenerateResponse]):
        for i in iter:
            yield i.model_dump_json()

    if stream:
        return StreamingResponse(content=streamer(resp))
    else:
        return JSONResponse(content=resp.model_dump())


@app.post("/api/embed")
async def embed(
    req: EmbedRequest,
):
    model = req.model
    try:
        client = await pick_random_supported_client(model=model)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

    resp = client.embed(**req.model_dump())

    return EmbedResponse(**resp.model_dump())


@app.post("/api/show")
async def show(req: ShowRequest):
    model = req.model
    try:
        client = await pick_random_supported_client(model=model)
    except ModelNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)

    resp = client.show(**req.model_dump())

    # resp attr is modelinfo, but the response object wants model_info
    return ShowResponse(**resp.model_dump(exclude="modelinfo"), model_info=resp.modelinfo)


@app.get("/", response_class=PlainTextResponse)
async def root() -> str:
    return "Ollama is running"


@app.get("/api/tags")
async def list_tags() -> CustomListResponse:
    await discover_hosts()
    # the distinct set of models for all hosts
    # metadata for the models is going to get smudged, unfortunately
    models = {}

    for client in clients.values():
        for model in client.models:
            # this is cursed, but basically since Models aren't hashable and I don't
            # feel like patching in frozen-ness, we're just going to take dict values
            models.update({model.model: model})

    return CustomListResponse(models=list(models.values()))
