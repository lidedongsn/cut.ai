from celery import Celery
from config.config_loader import REDIS_CONFIG

import sys
import os

print(sys.path)

host=os.getenv("REDIS_HOST", REDIS_CONFIG["host"])
port=os.getenv("REDIS_PORT", REDIS_CONFIG["port"])
database=os.getenv("REDIS_DB", REDIS_CONFIG["db"])
password=os.getenv("REDIS_PASSWORD", REDIS_CONFIG["password"])

app = Celery(
    "whisper_worker",
    broker=f"redis://:{password}@{host}:{port}/{database}",
    include=["fastapi_celery.tasks"],
)
# 配置 Celery 使用 Redis 作为结果后端
app.conf.result_backend = f"redis://:{password}@{host}:{port}/{database}"
