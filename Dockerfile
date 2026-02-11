# 1. Grab the Lambda Adapter binary
FROM public.ecr.aws/awsguru/aws-lambda-adapter:0.8.4 AS adapter

# 2. Use the official uv image as a builder for speed
FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim AS builder

# 3. Setup the build environment
WORKDIR /var/task
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy

# 4. Install dependencies FIRST (for better caching)
# Copy only the dependency files
COPY pyproject.toml uv.lock ./
# Install dependencies into a virtualenv (default is .venv)
RUN uv sync --frozen --no-install-project --no-dev

# 5. Final Stage (Smaller runtime image)
FROM python:3.12-slim

WORKDIR /var/task
COPY --from=adapter /lambda-adapter /opt/extensions/lambda-adapter

# Copy the virtual environment and your code from builder
COPY --from=builder /var/task/.venv /var/task/.venv
COPY src/ ./src/

# Ensure the virtualenv is used by default
ENV PATH="/var/task/.venv/bin:$PATH"
ENV PORT=8080

CMD ["python", "src/mcp_server.py"]