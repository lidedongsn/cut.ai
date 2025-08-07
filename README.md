# cut.ai

cut.ai 是一个AI音视频剪辑工具，语音转写基于whisper

## 功能列表

- [x] 语音转写
- [ ] 内容摘要总结
- [ ] 字幕剪辑
- [ ] 章节速览
- [ ] 精彩片段剪辑

## 环境安装

运行环境：python 3.10、redis
配置文件：`config.yaml`

``` shell
pip install -r requirements.txt
```

## 运行

### Server

分别执行
``` shell
uvicorn main:app --reload --host 0.0.0.0 --port 5010
```

``` shell
celery -A celery_config worker --loglevel=info 
```

### docker

``` shell
docker run -d --rm --gpus all -p 5010:5010 --name cut.ai-server -e "REDIS_HOST=192.168.4.9" -e "REDIS_PORT=6379" -e "REDIS_PASSWORD=lidedongsn" cut.ai-server:latest 
```

### Web
修改 `www/web/.env.development`文件中实际的 server 地址，并运行
VITE_BASE_URL='http://localhost:5010'

``` shell
npm run dev
```
浏览器打开 http://localhost:3004