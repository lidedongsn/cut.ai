[Read in Chinese (简体中文)](README.md)

# cut.ai

cut.ai is an AI-powered tool for audio/video editing, with speech-to-text functionality based on Whisper.

![Example](./assets/page.gif)


## Features

- [x] **Speech-to-Text**: High-accuracy speech recognition powered by Whisper.
- [x] **Waveform Player**: A modern, interactive audio player with waveform visualization, powered by `wavesurfer.js`.
- [x] **Synchronized Highlighting**: During playback, the transcript features dual-level highlighting for both phrases and individual words, with smooth auto-scrolling to keep the current focus in view.
- [x] **Click-to-Seek**: Click anywhere on the transcript to jump the audio playback to the corresponding moment.
- [x] **Inline Editing**: Edit the transcript directly on the page and save the changes back to the server.
- [ ] Content Summarization
- [ ] Subtitle Editing
- [ ] Chapter Overview
- [ ] Highlight Clipping

## Setup

### Backend (Server)

Environment: Python 3.10, Redis
Configuration File: `config.yaml`

``` shell
pip install -r server/requirements.txt
```

### Frontend (Web)

Environment: Node.js, pnpm

```shell
cd www/web
pnpm install
```

## Running the Project

### Server

Execute the following in two separate terminals:
``` shell
# Start the FastAPI service
uvicorn main:app --reload --host 0.0.0.0 --port 5010
```

``` shell
# Start the Celery worker
celery -A celery_config worker --loglevel=info --concurrency=4 
```

### Docker

``` shell
docker run -d --rm --gpus all -p 5010:5010 --name cut.ai-server -e "REDIS_HOST=192.168.4.9" -e "REDIS_PORT=6379" -e "REDIS_PASSWORD=lidedongsn" cut.ai-server:latest 
```

### Web
Modify the server address in `www/web/.env.development`:
`VITE_BASE_URL='http://localhost:5010'`

Then run:
``` shell
cd www/web
pnpm run dev
```
Open http://localhost:3000 in your browser.
