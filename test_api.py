#!/usr/bin/env python3
"""
测试IndexTTS API的功能
"""

import requests
import os
from pathlib import Path

def test_hello():
    """测试hello接口"""
    print("Testing /hello endpoint...")
    response = requests.get("http://localhost:8080/hello")
    if response.status_code == 200:
        print("✓ Hello endpoint works:", response.json())
    else:
        print("✗ Hello endpoint failed:", response.status_code)

def test_tts_create():
    """测试TTS创建接口"""
    print("\nTesting /tts/create endpoint...")
    
    data = {
        "text": "大家好，我现在正在测试IndexTTS API服务。",
        "gender": "female",
        "pitch": 3,
        "speed": 3,
        "idempotency_key": "test_create_001"
    }
    
    response = requests.post("http://localhost:8080/tts/create", data=data)
    
    if response.status_code == 200:
        # 保存返回的音频文件
        output_path = "test_create_output.wav"
        with open(output_path, "wb") as f:
            f.write(response.content)
        print(f"✓ TTS create endpoint works, saved to {output_path}")
        print(f"  File size: {len(response.content)} bytes")
    else:
        print("✗ TTS create endpoint failed:", response.status_code, response.text)

def test_tts_clone():
    """测试TTS克隆接口"""
    print("\nTesting /tts/clone endpoint...")
    
    # 使用项目中的示例音频文件
    prompt_audio_path = "tests/sample_prompt.wav"
    
    if not os.path.exists(prompt_audio_path):
        print("✗ Prompt audio file not found:", prompt_audio_path)
        return
    
    data = {
        "text": "这是一个语音克隆测试，使用IndexTTS API。",
        "prompt_text": "这是参考音频的文本。",
        "idempotency_key": "test_clone_001"
    }
    
    files = {
        "prompt_audio": ("sample_prompt.wav", open(prompt_audio_path, "rb"), "audio/wav")
    }
    
    try:
        response = requests.post("http://localhost:8080/tts/clone", data=data, files=files)
        
        if response.status_code == 200:
            # 保存返回的音频文件
            output_path = "test_clone_output.wav"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"✓ TTS clone endpoint works, saved to {output_path}")
            print(f"  File size: {len(response.content)} bytes")
        else:
            print("✗ TTS clone endpoint failed:", response.status_code, response.text)
    finally:
        files["prompt_audio"][1].close()

def test_tts_speed_pitch():
    """测试语速和音调调节功能"""
    print("\nTesting speed and pitch control...")
    
    base_text = "这是语速和音调测试："
    test_cases = [
        {"name": "最慢最低音", "speed": 1, "pitch": 1, "text": base_text + "最慢最低音"},
        {"name": "正常", "speed": 3, "pitch": 3, "text": base_text + "正常语速音调"},
        {"name": "最快最高音", "speed": 5, "pitch": 5, "text": base_text + "最快最高音"},
    ]
    
    for i, case in enumerate(test_cases):
        print(f"  Testing {case['name']}...")
        data = {
            "text": case["text"],
            "gender": "female",
            "pitch": case["pitch"],
            "speed": case["speed"],
            "idempotency_key": f"test_speed_pitch_{i}"
        }
        
        response = requests.post("http://localhost:8080/tts/create", data=data)
        
        if response.status_code == 200:
            output_path = f"test_{case['name'].replace(' ', '_')}_output.wav"
            with open(output_path, "wb") as f:
                f.write(response.content)
            print(f"    ✓ {case['name']} test passed, saved to {output_path}")
        else:
            print(f"    ✗ {case['name']} test failed:", response.status_code)

def main():
    """运行所有测试"""
    print("IndexTTS API 测试脚本")
    print("=" * 50)
    
    # 确保API服务已启动
    try:
        requests.get("http://localhost:8080/hello", timeout=5)
    except requests.exceptions.ConnectionError:
        print("✗ API服务未启动或无法连接到 http://localhost:8080")
        print("请先运行: python api.py")
        return
    
    test_hello()
    test_tts_create()
    test_tts_clone()
    test_tts_speed_pitch()
    
    print("\n测试完成！")

if __name__ == "__main__":
    main() 