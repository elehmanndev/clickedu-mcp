# clickedu-mcp served over streamable-http for the Unraid MCPHub route.
FROM ghcr.io/astral-sh/uv:bookworm-slim
WORKDIR /app
ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_INSTALL_DIR=/python
COPY pyproject.toml uv.lock ./
COPY src ./src
RUN uv sync --frozen --no-dev
ENV CLICKEDU_TRANSPORT=streamable-http \
    CLICKEDU_HTTP_HOST=0.0.0.0 \
    CLICKEDU_HTTP_PORT=8791 \
    CLICKEDU_COOKIE_PATH=/data/session.jar
EXPOSE 8791
CMD ["uv", "run", "--no-dev", "clickedu-mcp"]
