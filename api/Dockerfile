# ===== 构建阶段 =====
FROM python:3.13-slim-bookworm AS builder

# 用 pip 安装 uv（走阿里云 PyPI 镜像），避免从 ghcr.io 拉基础层卡死
ENV PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple/ \
    PIP_DISABLE_PIP_VERSION_CHECK=1
RUN pip install --no-cache-dir uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app/api

# 先安装依赖清单，充分利用 Docker 层缓存
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

# 拷贝源码并安装项目自身
COPY . .
RUN uv sync --frozen --no-dev

# ===== 生产阶段 =====
FROM python:3.13-slim-bookworm AS production

ENV FLASK_APP=app/http/app.py \
    FLASK_ENV=production \
    FLASK_DEBUG=0 \
    NLTK_DATA=/app/api/internal/core/unstructured/nltk_data \
    TZ=Asia/Shanghai \
    PATH="/app/api/.venv/bin:$PATH"

WORKDIR /app/api

# 只拷贝虚拟环境 + 源码 + 启动脚本，保持镜像精简
COPY --from=builder /app/api/.venv /app/api/.venv
COPY . /app/api
COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 5001
ENTRYPOINT ["/bin/bash", "/entrypoint.sh"]
