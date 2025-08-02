# tasks.py

from celery_config import app
from whisper import load_model
import os
from loguru import logger
import time
from db.redis import RedisHandler
from whisper.utils import get_writer
import wave
from moviepy import VideoFileClip

sync_redis = RedisHandler()


@app.task(bind=True)
def process_file_celery(self, file_id):
    try:
        task_id = self.request.id
        sync_redis.set_stt_task(
            task_id=task_id,
            task_info={"file_id": file_id, "state": "PROGRESS", "process": "init"},
        )
        file_info = sync_redis.get_file(file_id)
        if file_info is None:
            return None

        file_info["stt_task_id"] = task_id
        stt_file_name = file_info["file_path"]
        # 如果是视频文件，提取音频
        if file_info["file_type"].startswith("video/"):
            sync_redis.set_stt_task(
                task_id=task_id,
                task_info={
                    "file_id": file_id,
                    "state": "PROGRESS",
                    "process": "file_transcode",
                },
            )
            video_clip = VideoFileClip(file_info["file_path"])
            audio_clip = video_clip.audio
            stt_file_name = file_info["file_path"] + ".wav"
            audio_clip.write_audiofile(stt_file_name, codec="pcm_s16le")
            video_clip.close()
            audio_clip.close()

        file_info["stt_file_name"] = stt_file_name

        with wave.open(stt_file_name, "r") as wav_file:
            # 获取音频参数
            length = wav_file.getnframes()
            channels = wav_file.getnchannels()
            width = wav_file.getsampwidth()
            framerate = wav_file.getframerate()
            duration = length / float(framerate)
            file_info["audio_length"] = length
            file_info["audio_channels"] = channels
            file_info["audio_width"] = width
            file_info["audio_framerate"] = framerate
        logger.info(f"{task_id} 任务开始处理，文件信息：{file_info}")

        file_path = file_info["stt_file_name"]
        file_name = file_info["file_name"]

        sync_redis.add_file(file_id, file_info)

        T0 = time.time()
        sync_redis.set_stt_task(
            task_id=task_id,
            task_info={
                "file_id": file_id,
                "state": "PROGRESS",
                "process": "loading_model",
            },
        )
        model_name = "small"
        model = load_model(model_name)
        T1 = time.time()
        logger.info(f"加载模型耗时：{T1-T0}秒")
        # 使用 whisper 处理音频识别
        logger.info(f"开始处理文件：{file_path}")
        sync_redis.set_stt_task(
            task_id=task_id,
            task_info={
                "file_id": file_id,
                "state": "PROGRESS",
                "process": "processing_file",
            },
        )

        result = model.transcribe(
            file_path,
            fp16=False,
            language="Chinese",
            initial_prompt="以下是简体中文普通话的句子。",
            verbose=False,
        )
        T2 = time.time()
        logger.info(f"识别耗时：{T2-T1}秒")
        # 生成 SRT 字幕
        sync_redis.set_stt_task(
            task_id=task_id,
            task_info={
                "file_id": file_id,
                "state": "PROGRESS",
                "process": "generating_subtitle",
            },
        )
        writer = get_writer("srt", "./result")
        writer(
            result,
            f"{file_name}.srt",
            {"highlight_words": True, "max_line_count": 3, "max_line_width": 3},
        )
        T3 = time.time()
        logger.info(f"生成字幕耗时：{T3-T2}秒")

        text = result["text"]
        # 保存识别结果到Redis或mysql
        # 清理临时文件
        os.remove(file_path)
        logger.info(f"文件处理完毕：{file_path}")

        task_info = {}
        task_info["file_id"] = file_id
        task_info["file_name"] = file_name
        task_info["file_path"] = file_path
        task_info["duration"] = duration
        task_info["status"] = "success"
        task_info["process"] = "completed"
        task_info["cost_time"] = round(T3 - T0, 2)
        task_info["text"] = text
        task_info["state"] = "SUCCESS"

        sync_redis.set_stt_task(task_id=task_id, task_info=task_info)
    except Exception as e:
        logger.exception(e)  # 使用 loguru 记录异常
        sync_redis.set_stt_task(
            task_id=task_id,
            task_info={"file_id": file_id, "state": "FAILURE", "process": "failed"},
        )
    finally:
        # 确保所有临时文件都被清理
        if file_info["file_path"] != file_info["stt_file_name"]:
            if os.path.exists(file_info["stt_file_name"]):
                os.remove(file_info["stt_file_name"])


async def get_stt_progress(task_id):
    try:
        task = app.AsyncResult(task_id)
        return task
    except Exception as e:
        logger.exception(e)
        return None
