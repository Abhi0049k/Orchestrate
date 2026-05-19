FROM python:3.12-slim

# Install uv inside the container
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

# Copy the dependency management files
COPY pyproject.toml uv.lock* ./

# Install project dependencies into the container using uv
RUN uv sync --no-cache

# Copy the entire code repository (including faiss_db, agent, etc.)
COPY . .

EXPOSE 8000

# Run the FAISS FastAPI server using the uv environment
CMD ["uv", "run", "uvicorn", "faiss_db.main:app", "--host", "0.0.0.0", "--port", "8000"]
