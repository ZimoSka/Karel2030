# Karel 2030 — web backend + frontend v jednom image
FROM python:3.12-slim

WORKDIR /app

# Závislosti zvlášť — layer cache pri zmene kódu
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Aplikácia: core + server + frontend + jazykové súbory + svety
COPY karel_core/ karel_core/
COPY server/     server/
COPY static/     static/
COPY lang/       lang/
COPY worlds/     worlds/

# Persistentné dáta (assignments, links, workspaces) — mountovať volume
ENV KAREL_DATA_DIR=/data
ENV KAREL_LANG_DIR=/app/lang
VOLUME /data

EXPOSE 8000
CMD ["uvicorn", "server.app:app", "--host", "0.0.0.0", "--port", "8000"]
