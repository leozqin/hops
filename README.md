# HOPS
Heterogeneous Ollama Proxy Server (styled as HOPS or `hops`) is a load-balancing reverse proxy server that enables you to address a fleet of diverse/heterogeneous Ollama instances as a single one. 

The benefit of this approach is that you can scale inference throughput by using any cheap consumer-grade hardware, and you don't need to route inferences to different fleets based on their model needs nor acquire numerous of the same expensive GPUs. 

Instead, groups of like-minded individuals can pool their compute together and serve inferences with a shared goal in mind, or small institutions can create clusters using GPUs that they already have on hand.

Therefore, HOPS serves as a means to horizontally scale inference throughput (not vertically). Simply provision your Ollama instances with models that they can safely run, and HOPS will do the rest!

# How It Works/Featureset

When you request a model inference, HOPS transparently proxies the request to a server that has the model pulled. If more than one instance supports the model, HOPS will distribute requests among all the instances that support that model.

Currently, load balancing is done using randomization, but future load-balancing strategies include round-robin and memory-aware dynamic modes (prioritize Ollama instances that are likely to have the model loaded in memory, at the cost of additional metadata queries). 

Intuitively, we'll also need to build a facility for retries and suspending unavailable hosts from the pool.

Hosts are enumerated by describing them in a `yml` file. See the Deployment section for an example of such a file.

# API Coverage

Currently, HOPS is known to be functional with `v0.5.4` of Ollama, and the following Ollama REST endpoints are transparently implemented in HOPS:
1. `POST /api/generate` (single response and streaming)
2. `POST /api/chat` (single response and streaming)
3. `POST /api/embed`
4. `GET /api/tags` - returns the superset of models available across all known hosts
5. `POST /api/show` - returns the first instance of the specified model that the cluster supports

# Deployment using Docker Compose
First, create a `hosts.yml` that looks like below:
```yaml
- id: ollama0
  host: http://ollama0:11434
```

Each host entry is deserialized and passed directly to `ollama.Client`, which in turn passes them to [`httpx.Client`](https://www.python-httpx.org/api/#client) - so, you can pass additional args as necessary to set headers, timeouts, etc... 

Then, modify the docker-compose file to mount this file in the container, and set the `HOSTS` variable to the path of the file you created.

Finally, run `docker compose up`

# Dev
`hops` is built on Python 3.12. I recommend to install this using `pyenv` or similar. Alternatively, if you're using Nix, do `nix develop` to start a dev shell.

Then, create a fresh venv, activate it, and do `pip install -r requirements.txt`. Then, create a `hosts.yml` file in the `data` dir in the repo (it is `.gitignore`-d), or set the `OLLAMA_HOSTS` environment variable to point to this file.

To start the server, do `fastapi dev`. The server will start on port 11434, as is convention for Ollama.