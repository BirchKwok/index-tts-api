FROM python:3.10-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt requirements_api.txt ./

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements_api.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8080

# 创建输出目录
RUN mkdir -p outputs/api

# 设置环境变量
ENV PYTHONPATH=/app

# 启动命令
CMD ["python", "api.py", "--host", "0.0.0.0", "--port", "8080"] 