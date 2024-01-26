# cut.ai

cut.ai 是一个AI音视频剪辑工具，语音转写基于whisper

## 功能列表

- [x] 语音转写
- [ ] 内容摘要总结
- [ ] 字幕剪辑
- [ ] 章节速览
- [ ] 精彩片段剪辑

## 模块

### Server

``` shell
uvicorn main:app --reload --host 0.0.0.0 --port 5001
```

``` shell
celery -A celery_config worker --loglevel=info 
```



### Web
