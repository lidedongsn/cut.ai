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
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter()
sync_redis = RedisHandler()


class UpdateTranscriptRequest(BaseModel):
    task_id: str
    segments: List[Dict[str, Any]]


@router.post("/upload")
async def file_upload(file: UploadFile = File(...)):
    # 检查上传的文件类型
    if not file.content_type.startswith(("audio/", "video/")):
        raise HTTPException(status_code=400, detail="只能上传音频或视频文件。")

    try:
        current_time = datetime.now()
        formatted_current_time = current_time.strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]
        storage_dir = "storage"
        os.makedirs(storage_dir, exist_ok=True)

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
        logger.exception(e)
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)
        raise HTTPException(status_code=500, detail="文件上传失败")


@router.post("/stt")
async def stt_task(file_id: str = Form(...)):
    try:
        logger.info(f"开始处理文件：{file_id}")
        task = process_file_celery.delay(file_id)
        # 将任务ID添加到全局列表
        sync_redis.add_task_to_global_list(task.id)
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
                        "file_name": task_info["file_name"],
                        "file_path": task_info.get("file_path"),
                        "file_type": task_info.get("file_type"),
                        "text": task_info["text"],
                        "segments": task_info["segments"],
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


@router.post("/stt-update")
async def update_stt_task(request: UpdateTranscriptRequest):
    try:
        task_info = sync_redis.get_stt_task(request.task_id)
        if task_info is None:
            raise HTTPException(status_code=404, detail="Task not found")

        task_info["segments"] = request.segments

        for segment in task_info["segments"]:
            segment["text"] = "".join(
                [word["word"] for word in segment["words"]]
            ).strip()

        task_info["text"] = "\n\n".join([s["text"] for s in task_info["segments"]])

        sync_redis.set_stt_task(request.task_id, task_info)

        return JSONResponse(
            content={"code": 200, "message": "Transcript updated successfully"}
        )
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Failed to update transcript")


@router.get("/stt-tasks")
async def get_all_stt_tasks():
    try:
        task_ids = sync_redis.get_all_task_ids_from_global_list()
        valid_tasks = []
        for task_id in task_ids:
            task_info = sync_redis.get_stt_task(task_id)

            if not task_info:
                continue

            if task_info.get("state") != "SUCCESS":
                continue

            file_path = task_info.get("file_path")
            if not file_path or not os.path.exists(file_path):
                continue

            if not all(k in task_info for k in ["file_name", "duration", "segments"]):
                continue

            task_info["task_id"] = task_id
            valid_tasks.append(task_info)

        return JSONResponse(
            content={"code": 200, "message": "Success", "data": valid_tasks}
        )

    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Failed to retrieve tasks")


@router.delete("/stt-task/{task_id}")
async def delete_stt_task(task_id: str):
    try:
        task_info = sync_redis.get_stt_task(task_id)
        if not task_info:
            raise HTTPException(status_code=404, detail="Task not found")

        srt_path = task_info.get("srt_path")
        if srt_path and os.path.exists(srt_path):
            try:
                os.remove(srt_path)
                logger.info(f"Deleted SRT file: {srt_path}")
            except Exception as srt_del_error:
                logger.error(f"Error deleting SRT file {srt_path}: {srt_del_error}")

        file_path = task_info.get("file_path")
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
                logger.info(f"Deleted media file: {file_path}")
            except Exception as file_del_error:
                logger.error(f"Error deleting file {file_path}: {file_del_error}")

        sync_redis.delete_stt_task(task_id)

        file_id = task_info.get("file_id")
        if file_id:
            sync_redis.delete_file(file_id)

        sync_redis.remove_task_from_global_list(task_id)

        logger.info(f"Successfully deleted task {task_id} and associated data.")
        return JSONResponse(
            content={"code": 200, "message": "Task deleted successfully"}
        )

    except HTTPException as http_exc:
        raise http_exc
    except Exception as e:
        logger.exception(e)
        raise HTTPException(status_code=500, detail="Failed to delete task")
