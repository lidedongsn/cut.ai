from celery_config import app
from whisper import load_model
import os
from loguru import logger
import time
from db.redis import RedisHandler
from whisper.utils import get_writer
import wave
from moviepy import VideoFileClip
from datetime import datetime

sync_redis = RedisHandler()

import torch

model = None
model_name = "small"


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

        global model
        if model is None:
            torch.set_num_threads(os.cpu_count())
            model = load_model(model_name)

        if stt_file_name.lower().endswith(".wav"):
            with wave.open(stt_file_name, "r") as wav_file:
                length = wav_file.getnframes()
                channels = wav_file.getnchannels()
                width = wav_file.getsampwidth()
                framerate = wav_file.getframerate()
                duration = length / float(framerate)
                file_info["audio_length"] = length
                file_info["audio_channels"] = channels
                file_info["audio_width"] = width
                file_info["audio_framerate"] = framerate
        else:
            from pydub import AudioSegment

            audio = AudioSegment.from_file(stt_file_name)
            duration = len(audio) / 1000.0
            file_info["audio_length"] = len(audio.get_array_of_samples())
            file_info["audio_channels"] = audio.channels
            file_info["audio_width"] = audio.sample_width
            file_info["audio_framerate"] = audio.frame_rate

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
        T1 = time.time()
        logger.info(f"加载模型耗时：{T1-T0}秒")
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
            temperature=0,
            language="Chinese",
            initial_prompt="以下是简体中文普通话的句子。",
            verbose=False,
            word_timestamps=True,  # 获取每个词的时间戳
        )
        T2 = time.time()
        logger.info(f"识别耗时：{T2-T1}秒")

        segments = result["segments"]
        formatted_text = "\n\n".join([s["text"] for s in segments])

        sync_redis.set_stt_task(
            task_id=task_id,
            task_info={
                "file_id": file_id,
                "state": "PROGRESS",
                "process": "generating_subtitle",
            },
        )

        base_processed_filename = os.path.basename(file_path)
        srt_filename = f"{base_processed_filename}.srt"
        srt_output_dir = "./result"
        srt_file_path = os.path.join(srt_output_dir, srt_filename)

        writer = get_writer("srt", srt_output_dir)
        writer(
            result,
            srt_filename,
            # {"highlight_words": True, "max_line_count": 3, "max_line_width": 3},
        )
        T3 = time.time()
        logger.info(f"生成字幕耗时：{T3-T2}秒")

        # os.remove(file_path)
        logger.info(f"文件处理完毕：{file_path}")

        task_info = {}
        task_info["completion_time"] = datetime.now().isoformat()
        task_info["file_id"] = file_id
        task_info["file_type"] = file_info.get("file_type")
        task_info["file_name"] = file_name
        task_info["file_path"] = file_info["file_path"]
        task_info["duration"] = duration
        task_info["srt_path"] = srt_file_path
        task_info["status"] = "success"
        task_info["process"] = "completed"
        task_info["cost_time"] = round(T3 - T0, 2)
        task_info["text"] = formatted_text
        task_info["segments"] = segments
        task_info["state"] = "SUCCESS"

        sync_redis.set_stt_task(task_id=task_id, task_info=task_info)
    except Exception as e:
        logger.exception(e)
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
