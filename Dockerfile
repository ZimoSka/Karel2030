# Karel 2030 — web backend + frontend v jednom image
FROM python:3.12-slim

WORKDIR /app

# Závislosti zvlášť — layer cache pri zmene kódu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Aplikácia: core + server + frontend + jazykové súbory + svety + verzia
COPY karel_core/ karel_core/
COPY server/     server/
COPY static/     static/
COPY lang/       lang/
COPY worlds/     worlds/
COPY examples/   examples/
COPY VERSION     VERSION

# Verzia buildu — odovzdané cez --build-arg (git SHA, čas)
ARG GIT_SHA=dev
ARG BUILD_TIME=
ENV KAREL_GIT_SHA=${GIT_SHA}
ENV KAREL_BUILD_TIME=${BUILD_TIME}

# Persistentné dáta (assignments, links, workspaces) — mountovať volume
ENV KAREL_DATA_DIR=/data
ENV KAREL_LANG_DIR=/app/lang
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
