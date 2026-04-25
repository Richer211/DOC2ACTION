# Doc2Action API — minimal image for Railway / Fly / ECS 等容器平台
FROM python:3.12-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Railway 等平台注入 PORT；本地默认 8000
EXPOSE 8000
# echo + --log-level info：便于 Railway「Deploy Logs」里看到启动行（否则常像「完全没日志」）
CMD ["sh", "-c", "echo \"[doc2action] starting uvicorn on 0.0.0.0:${PORT:-8000}\" && exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --log-level info"]
