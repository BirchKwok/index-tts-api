# IndexTTS API 服务

基于IndexTTS模型的FastAPI服务，提供与SparkTTS API兼容的接口。

## 功能特性

- 🎯 **兼容接口**: 保持与SparkTTS API相同的接口名称和结构
- 🚀 **高性能**: 基于IndexTTS-1.5模型，提供工业级的TTS服务
- 🔄 **幂等性**: 支持idempotency_key，避免重复请求
- 🎵 **语音克隆**: 支持零样本语音克隆功能
- 🎛️ **语音控制**: 支持语速和音调调节
- 📝 **详细日志**: 提供完整的推理过程日志

## 快速开始

### 1. 环境准备

确保已安装IndexTTS依赖：

```bash
# 安装依赖
pip install -r requirements.txt

# 下载模型 (如果还没有)
huggingface-cli download IndexTeam/IndexTTS-1.5 \
  config.yaml bigvgan_discriminator.pth bigvgan_generator.pth bpe.model dvae.pth gpt.pth unigram_12000.vocab \
  --local-dir checkpoints
```

### 2. 启动API服务

```bash
# 使用默认配置启动
python api.py

# 或指定参数
python api.py --host 0.0.0.0 --port 8080 --model_dir checkpoints
```

### 3. 测试API

```bash
# 运行测试脚本
python test_api.py
```

## API 接口

### 1. 健康检查

```http
GET /hello
```

返回服务状态信息。

### 2. 语音合成

```http
POST /tts/create
```

**参数:**
- `text` (string): 要合成的文本
- `gender` (string): 性别 ("male" 或 "female") - *注意：IndexTTS通过参考音频控制音色*
- `pitch` (int): 音调 (1=最低, 5=最高) - *现已支持*
- `speed` (int): 语速 (1=最慢, 5=最快) - *现已支持*
- `idempotency_key` (string, 可选): 幂等性键

**示例:**

```bash
curl -X POST "http://localhost:8080/tts/create" \
  -F "text=大家好，我现在正在测试IndexTTS API。" \
  -F "gender=female" \
  -F "pitch=3" \
  -F "speed=3" \
  -F "idempotency_key=test_001" \
  --output output.wav
```

### 3. 语音克隆

```http
POST /tts/clone
```

**参数:**
- `text` (string): 要合成的文本
- `prompt_audio` (file): 参考音频文件
- `prompt_text` (string, 可选): 参考音频的文本内容
- `gender` (string, 可选): 性别 - *通过参考音频控制*
- `pitch` (int, 可选): 音调 (1=最低, 5=最高) - *现已支持*
- `speed` (int, 可选): 语速 (1=最慢, 5=最快) - *现已支持*
- `idempotency_key` (string, 可选): 幂等性键

**示例:**

```bash
curl -X POST "http://localhost:8080/tts/clone" \
  -F "text=这是一个语音克隆测试。" \
  -F "prompt_audio=@tests/sample_prompt.wav" \
  -F "prompt_text=参考音频的文本内容" \
  -F "idempotency_key=clone_001" \
  --output cloned_output.wav
```

## Python 客户端示例

```python
import requests

# 语音合成
def create_tts(text, gender="female", pitch=3, speed=3):
    data = {
        "text": text,
        "gender": gender,
        "pitch": pitch,
        "speed": speed
    }
    
    response = requests.post("http://localhost:8080/tts/create", data=data)
    
    if response.status_code == 200:
        with open("output.wav", "wb") as f:
            f.write(response.content)
        print("音频已保存到 output.wav")
    else:
        print("请求失败:", response.text)

# 语音克隆
def clone_voice(text, prompt_audio_path, prompt_text=None):
    data = {
        "text": text,
        "prompt_text": prompt_text or ""
    }
    
    files = {
        "prompt_audio": ("audio.wav", open(prompt_audio_path, "rb"), "audio/wav")
    }
    
    try:
        response = requests.post("http://localhost:8080/tts/clone", data=data, files=files)
        
        if response.status_code == 200:
            with open("cloned_output.wav", "wb") as f:
                f.write(response.content)
            print("克隆音频已保存到 cloned_output.wav")
        else:
            print("请求失败:", response.text)
    finally:
        files["prompt_audio"][1].close()

# 使用示例
create_tts("Hello, this is a test.")
clone_voice("这是克隆测试", "tests/sample_prompt.wav")
```

## 语速和音调控制示例

```python
import requests

def test_speed_pitch_control():
    """测试语速和音调控制功能"""
    
    # 测试不同语速
    speed_tests = [
        {"speed": 1, "text": "这是最慢的语速测试", "name": "最慢"},
        {"speed": 3, "text": "这是正常的语速测试", "name": "正常"},
        {"speed": 5, "text": "这是最快的语速测试", "name": "最快"},
    ]
    
    for test in speed_tests:
        data = {
            "text": test["text"],
            "gender": "female",
            "pitch": 3,  # 正常音调
            "speed": test["speed"]
        }
        
        response = requests.post("http://localhost:8080/tts/create", data=data)
        if response.status_code == 200:
            with open(f"speed_{test['name']}.wav", "wb") as f:
                f.write(response.content)
            print(f"✓ {test['name']}语速测试完成")
    
    # 测试不同音调
    pitch_tests = [
        {"pitch": 1, "text": "这是最低音调测试", "name": "最低音"},
        {"pitch": 3, "text": "这是正常音调测试", "name": "正常音"},
        {"pitch": 5, "text": "这是最高音调测试", "name": "最高音"},
    ]
    
    for test in pitch_tests:
        data = {
            "text": test["text"],
            "gender": "female",
            "pitch": test["pitch"],
            "speed": 3  # 正常语速
        }
        
        response = requests.post("http://localhost:8080/tts/create", data=data)
        if response.status_code == 200:
            with open(f"pitch_{test['name']}.wav", "wb") as f:
                f.write(response.content)
            print(f"✓ {test['name']}调测试完成")

# 运行测试
test_speed_pitch_control()
```

## 配置参数

启动API时可以使用以下参数：

- `--model_dir`: 模型目录路径 (默认: checkpoints)
- `--device`: GPU设备ID (默认: 0)
- `--host`: 服务主机地址 (默认: 0.0.0.0)
- `--port`: 服务端口 (默认: 8080)
- `--output_dir`: 输出音频目录 (默认: outputs/api)

## 注意事项

1. **音色控制**: IndexTTS主要通过参考音频控制音色，gender参数通过参考音频实现
2. **语速控制**: 支持1-5级语速调节，通过调节模型的generation参数实现
3. **音调控制**: 支持1-5级音调调节，通过调节模型的generation参数实现
4. **默认参考音频**: `/tts/create`接口使用`tests/sample_prompt.wav`作为默认参考音频
5. **文件清理**: 临时上传的参考音频文件会在处理后自动删除
6. **幂等性**: 使用相同的`idempotency_key`会返回缓存结果
7. **性能**: 首次加载模型可能需要一些时间，后续推理会比较快

## 错误处理

常见错误码：
- `400`: 参数验证失败
- `500`: TTS推理失败
- `503`: 模型未加载完成

## 日志

API服务会输出详细的日志信息，包括：
- 模型加载状态
- 推理时间统计
- 文件保存路径
- 错误信息

查看日志可以帮助调试问题和监控性能。 