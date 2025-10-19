# 允许通过构建参数切换基础镜像（例如使用国内镜像加速）
ARG PY_BASE=python:3.11-slim
FROM ${PY_BASE}

# 基本环境变量：减少缓存与加快启动
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# 先复制依赖文件以利用 Docker 层缓存
COPY requirements.txt ./

# 如遇到无预编译轮子导致安装失败，可取消注释下方 apt 依赖
# 仅在必要时开启，以保持镜像体积可控
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential gcc g++ curl \
#     && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

# 复制源码
COPY . .

EXPOSE 3000

# 以 SSE 模式启动服务，监听 0.0.0.0:3000
CMD ["python", "main.py", "--sse", "--host", "0.0.0.0", "--port", "3000"]
