FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.8.15 /uv /uvx /bin/

# Cài các thư viện hệ thống mà OpenCV cần
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 libsm6 libxrender1 libxext6 \
    && rm -rf /var/lib/apt/lists/*

ADD . /src

WORKDIR /src
RUN uv sync --locked --no-dev --compile-bytecode

ENV PATH="/src/.venv/bin:$PATH"

# Expose the port the app runs on
EXPOSE 8000

# Command to run the application
CMD ["fastapi", "run"]