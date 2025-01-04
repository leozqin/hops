FROM ollama/ollama:0.5.4 as ollama
FROM cgr.dev/chainguard/wolfi-base

RUN apk add --no-cache libstdc++
COPY --from=ollama /usr/bin/ollama /usr/bin/ollama
COPY --from=ollama /usr/lib/ollama/runners /usr/lib/ollama/runners

ARG OLLAMA_MODEL_TAG
RUN /usr/bin/ollama serve & sleep 5 && \
      /usr/bin/ollama pull $OLLAMA_MODEL_TAG

ENV OLLAMA_HOST=0.0.0.0

EXPOSE 11434
ENTRYPOINT ["/usr/bin/ollama"]
CMD ["serve"]