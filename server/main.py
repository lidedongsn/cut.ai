from fastapi import FastAPI,Request
from fastapi.middleware.cors import CORSMiddleware

from api.stt import router as stt
import logging
from loguru import logger
import time
import sys

# 配置Loguru日志器，添加控制台和文件输出
# logger.add("logs/cutai_{time}.log", rotation="1 day")  # 每天轮换日志文件
logger.add(sys.stderr, format="{time} {level} {message}", filter="my_module", level="INFO")  # 控制台输出

# 创建日志实例
class InterceptHandler(logging.Handler):
    def emit(self, record):
        # 获取对应的 Loguru 日志级别
        level = logger.level(record.levelname).name
        # 将消息转发到 Loguru，包括调用者信息
        logger.opt(depth=6).log(level, record.getMessage())


# logging.basicConfig(handlers=[InterceptHandler()], level=0)

logger_name_list = [name for name in logging.root.manager.loggerDict]

for logger_name in logger_name_list:
    logging.getLogger(logger_name).setLevel(0)
    logging.getLogger(logger_name).handlers = []
    if "." not in logger_name:
        logging.getLogger(logger_name).addHandler(InterceptHandler())
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://172.16.22.193:3000"],  # 允许的源列表，可以使用 ['*'] 来允许所有源
    allow_credentials=True,
    allow_methods=["*"],  # 允许的方法列表，['*'] 表示允许所有 HTTP 方法
    allow_headers=["*"],  # 允许的头信息列表，['*'] 表示允许所有头
)
app.include_router(stt, prefix="/api", tags=["语音转写"])


async def on_startup():
    logger.info("应用启动，列出所有路由：")
    for route in app.routes:
        methods = ",".join(route.methods)
        route_details = f"路由: {route.path}, 方法: {methods}"
        logger.info(route_details)


async def on_shutdown():
    logger.info("应用关闭")


# 注册生命周期事件处理器
app.router.add_event_handler("startup", on_startup)
app.router.add_event_handler("shutdown", on_shutdown)

# 定义中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # 请求开始时记录
    logger.info(f"请求开始: {request.method} {request.url}")
    start_time = time.time()
    
    # 处理请求
    response = await call_next(request)
    
    # 请求结束时记录
    process_time = (time.time() - start_time) * 1000
    logger.info(f"请求结束: {request.method} {request.url} 完成于 {process_time}ms 状态码: {response.status_code}")
    
    return response