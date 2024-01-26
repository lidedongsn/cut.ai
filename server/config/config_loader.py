# config_loader.py
import yaml

def load_config(file_path):
    with open(file_path, 'r') as file:
        return yaml.safe_load(file)

# 加载配置文件
config = load_config('./config/config.yaml')

# 提取配置信息
DATABASE_CONFIG = config.get('database', {})
REDIS_CONFIG = config.get('redis', {})
API_CONFIG = config.get('api', {})
