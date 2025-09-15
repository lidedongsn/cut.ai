import datetime
from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Form
from moviepy import VideoFileClip, AudioFileClip
from loguru import logger
import os
from datetime import datetime
from fastapi_celery.tasks import process_file_celery, get_stt_progress
import uuid
from db.redis import RedisHandler

router = APIRouter()
sync_redis = RedisHandler()


@router.post("/upload")
async def file_upload(file: UploadFile = File(...)):
    # 检查上传的文件类型
    if not file.content_type.startswith(("audio/", "video/")):
        raise HTTPException(status_code=400, detail="只能上传音频或视频文件。")

    try:
        # 获取当前时间
        current_time = datetime.now()

        # 格式化时间
        formatted_current_time = current_time.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
        # 指定存储目录
        storage_dir = "storage"  # 你可以根据需要修改这个目录路径
        os.makedirs(storage_dir, exist_ok=True)  # 确保目录存在，如果不存在则创建

        # 保存文件到指定的存储目录中
        temp_file_path = os.path.join(
            storage_dir, f"{formatted_current_time}_{file.filename}"
        )
        with open(temp_file_path, "wb") as f:
            f.write(await file.read())

        file_id = str(uuid.uuid4())
        file_info = {}
        file_info["file_id"] = file_id
        file_info["file_name"] = file.filename
        file_info["file_path"] = temp_file_path
        file_info["file_size"] = file.size
        file_info["file_type"] = file.content_type

        # 如果是视频文件，提取音频
        if file.content_type.startswith("video/"):
            video_clip = VideoFileClip(temp_file_path)
            file_info["duration"] = video_clip.duration
        elif file.content_type.startswith("audio/"):
            audio_clip = AudioFileClip(temp_file_path)
            file_info["duration"] = audio_clip.duration

        sync_redis.add_file(file_id, file_info)

        return JSONResponse(
            content={
                "code": 200,
                "message": "文件上传成功",
                "data": {"file_id": file_id},
            }
        )
    except Exception as e:
        logger.exception(e)  # 使用 loguru 记录异常
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail="文件上传失败")


@router.post("/stt")
async def stt_task(file_id: str = Form(...)):
    try:
        logger.info(f"开始处理文件：{file_id}")
        task = process_file_celery.delay(file_id)
        return JSONResponse(
            content={
                "code": 200,
                "message": "文件正在后台处理",
                "data": {"task_id": task.id},
            }
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="文件处理失败")


@router.get("/stt-progress/{task_id}")
async def get_stt_result(task_id: str):
    try:
        task_info = sync_redis.get_stt_task(task_id)
        # logger.info(f"获取任务结果：{task_info}")
        if task_info is None:
            return JSONResponse(content={"code": 404, "message": "任务不存在"})
        if task_info["state"] == "SUCCESS":
            return JSONResponse(
                content={
                    "code": 200,
                    "message": "文件处理完成",
                    "data": {
                        "task_id": task_id,
                        "text": task_info["text"],
                        "segments": task_info["segments"],
                        "file_name": task_info["file_name"],
                        "file_path": task_info["file_path"],
                    },
                }
            )
        elif task_info["state"] == "FAILURE":
            return JSONResponse(
                content={
                    "code": 110001,
                    "message": "文件处理失败",
                    "data": {"task_id": task_id},
                }
            )
        else:
            return JSONResponse(
                content={
                    "code": 100001,
                    "message": "文件处理中",
                    "data": {"task_id": task_id},
                }
            )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="获取文件处理结果失败")
