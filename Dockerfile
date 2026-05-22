# Use Python 3.12 slim image for smaller size
FROM python:3.12-slim

WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_SYSTEM_PYTHON=1

# Copy dependency files
COPY pyproject.toml README.md ./

# Copy source code
COPY src/ ./src/

# Install garmin_mcp dependencies
RUN uv pip install -e .

# Install SSE wrapper dependencies
RUN uv pip install starlette uvicorn python-dotenv

# Copy your custom logic and SSE wrapper
COPY custom/ ./custom/
COPY sse_wrapper.py ./

# Create directory for Garmin tokens
RUN mkdir -p /root/.garminconnect && \
    chmod 700 /root/.garminconnect

# Expose port for SSE
EXPOSE 8000

# Run the SSE wrapper instead of stdio garmin-mcp
CMD ["python3", "sse_wrapper.py"]