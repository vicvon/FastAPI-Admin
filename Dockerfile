FROM python:3.11-slim

WORKDIR /app

ENV TZ=Asia/Shanghai \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    UV_LINK_MODE=copy \
    PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH="/app/backend"

COPY pyproject.toml uv.lock ./
COPY backend ./backend

RUN pip install uv --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple/
RUN uv sync --frozen --no-dev --package backend -i https://pypi.tuna.tsinghua.edu.cn/simple/

EXPOSE 8000

WORKDIR /app/backend

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
