from celery import Celery
from config.config_loader import REDIS_CONFIG

import sys

print(sys.path)

host = REDIS_CONFIG["host"]
port = REDIS_CONFIG["port"]
password = REDIS_CONFIG["password"]
database = REDIS_CONFIG["db"]
app = Celery(
    "whisper_worker",
    broker=f"redis://:{password}@{host}:{port}/{database}",
    include=["fastapi_celery.tasks"],
)
# 配置 Celery 使用 Redis 作为结果后端
app.conf.result_backend = f"redis://:{password}@{host}:{port}/{database}"
