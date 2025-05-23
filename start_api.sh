#!/bin/bash

# IndexTTS API 启动脚本

set -e

echo "IndexTTS API 启动脚本"
echo "===================="

# 检查模型文件
echo "检查模型文件..."
if [ ! -d "checkpoints" ]; then
    echo "错误: checkpoints 目录不存在"
    echo "请先下载模型文件到 checkpoints 目录"
    exit 1
fi

required_files=("config.yaml" "gpt.pth" "bigvgan_generator.pth" "bpe.model")
for file in "${required_files[@]}"; do
    if [ ! -f "checkpoints/$file" ]; then
        echo "错误: 缺少模型文件 checkpoints/$file"
        echo "请下载完整的模型文件"
        exit 1
    fi
done

echo "✓ 模型文件检查完成"

# 检查API依赖
echo "检查依赖..."
python -c "import fastapi, uvicorn" 2>/dev/null || {
    echo "缺少API依赖，正在安装..."
    pip install -r requirements_api.txt
}

echo "✓ 依赖检查完成"

# 创建输出目录
mkdir -p outputs/api

# 启动API服务
echo "启动API服务..."
echo "服务地址: http://localhost:8080"
echo "API文档: http://localhost:8080/docs"
echo "按 Ctrl+C 停止服务"
echo ""

python api.py "$@" 