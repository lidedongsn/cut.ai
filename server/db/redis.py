import json
import redis
from config.config_loader import REDIS_CONFIG
from loguru import logger


class RedisHandler:
    def __init__(
        self,
        host=REDIS_CONFIG["host"],
        port=REDIS_CONFIG["port"],
        db=REDIS_CONFIG["db"],
        password=REDIS_CONFIG["password"],
    ):
        self.host = host
        self.port = port
        self.db = db | 0
        self.password = password
        self.redis_pool = None
        self.redis_client = None
        self.FILEKEY_PREFIX = "cutai:files:"
        self.TASKKEY_PREFIX = "cutai:tasks:"
        self.connect()

    def connect(self):
        print(REDIS_CONFIG)
        logger.info("load redis config", REDIS_CONFIG)
        self.redis_pool = redis.ConnectionPool.from_url(
            f"redis://{self.host}:{self.port}/{self.db}",
            password=self.password,
        )
        self.redis_client = redis.Redis(connection_pool=self.redis_pool)
        if self.redis_client.ping():
            logger.info("redis connect success")
        else:
            logger.error("redis connect failed")

    def disconnect(self):
        if self.redis_client:
            self.redis_client.close()
        if self.redis_pool:
            self.redis_pool.disconnect()

    def store_message(self, conversation_key, message):
        try:
            self.redis_client.rpush(conversation_key, message)
            self.redis_client.expire(conversation_key, 3600 * 24 * 7)

        except Exception as e:
            logger.error(f"Error storing message: {e}")

    def retrieve_messages(self, conversation_key, start=0, end=-1):
        try:
            messages = self.redis_client.lrange(conversation_key, start, end)
            return [message.decode("utf-8") for message in messages]
        except Exception as e:
            logger.error(f"Error retrieving messages: {e}")
            return []

    def add_file(self, file_id, file_info):
        try:
            self.redis_client.setex(
                self.FILEKEY_PREFIX + file_id, 3600 * 24 * 7, json.dumps(file_info)
            )
        except Exception as e:
            logger.error(f"Error adding file: {e}")

    def get_file(self, file_id):
        try:
            file_info_str = self.redis_client.get(self.FILEKEY_PREFIX + file_id)
            if file_info_str:
                return json.loads(file_info_str)
            return None
        except Exception as e:
            logger.error(f"Error getting file: {e}")
            return None

    def delete_file(self, file_id):
        try:
            self.redis_client.delete(file_id)
        except Exception as e:
            logger.error(f"Error deleting file: {e}")
    
    def set_stt_task(self, task_id, task_info):
        try:
            self.redis_client.setex(
                self.TASKKEY_PREFIX + task_id, 3600 * 24 * 7, json.dumps(task_info))
        except Exception as e:
            logger.error(f"Error setting STT task: {e}")

    def get_stt_task(self, task_id):
        try:
            task_info_str = self.redis_client.get(self.TASKKEY_PREFIX + task_id)
            if task_info_str:
                return json.loads(task_info_str)
            return None
        except Exception as e:
            logger.error(f"Error getting STT task: {e}")
            return None
