# HOPS
Heterogenous Ollama Proxy Server (styled as HOPS or `hops`) is a load-balancing reverse proxy server that enables you to address a fleet of diverse/heterogenous Ollama instances as a single one. 

The benefit of this approach is that you can scale inference throughput by using any cheap consumer-grade hardware, and you don't need to route inferences to different fleets based on their model needs nor acquire numerous of the same expensive GPUs. 

Instead, groups of like-minded individuals can pool their compute together and serve inferences with a shared goal in mind, or small institutions can create clusters using GPUs that they already have on hand.

Therefore, HOPS serves as a means to horizontally scale inference throughput (not vertically). Simply provision your Ollama instances with models that they can safely run, and HOPS will do the rest!

# How It Works/Featureset

When you request a model inference, HOPS transparently proxies the request to a server that has the model pulled. If more than one instance supports the model, HOPS will distribute requests among all the instances that support that model.

Currently, load balancing is done using randomization, but future load-balancing strategies include round-robin and memory-aware dynamic modes (prioritize Ollama instances that are likely to have the model loaded in memory, at the cost of additional metadata queries). 

Intuitively, we'll also need to build a facility for retries and suspending unavailable hosts from the pool.

# API Coverage

Currently, HOPS is known to be functional with `v0.5.4` of Ollama, and the following Ollama REST endpoints are transparently implemented in HOPS:
1. `POST /api/generate` (single response and streaming)
2. `POST /api/chat` (single response and streaming)
3. `POST /api/embed`
4. `GET /api/tags` - returns the superset of models available across all known hosts
5. `POST /api/show` - returns the first instance of the specified model that the cluster supports