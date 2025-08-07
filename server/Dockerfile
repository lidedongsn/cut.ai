FROM python:3.10

# 确保CUDA环境变量正确
ENV PATH="/usr/local/cuda/bin:${PATH}"
ENV LD_LIBRARY_PATH="/usr/local/cuda/lib64:${LD_LIBRARY_PATH}"
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

WORKDIR /app

# 配置pip国内源（阿里云）
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set global.trusted-host mirrors.aliyun.com 

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 安装ffmpeg supervisor
RUN apt-get update && apt-get install -y \
    ffmpeg \
    supervisor && \
    mkdir -p /var/run /var/log/supervisor

# 复制supervisor配置文件
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# 暴露端口
EXPOSE 5010

# 启动supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]
