#!/usr/bin/env python3
"""
IndexTTS API 客户端示例
"""

import requests
import os
import time

class IndexTTSClient:
    def __init__(self, base_url="http://localhost:8080"):
        self.base_url = base_url
    
    def health_check(self):
        """检查服务状态"""
        try:
            response = requests.get(f"{self.base_url}/hello")
            return response.status_code == 200, response.json()
        except Exception as e:
            return False, str(e)
    
    def create_tts(self, text, gender="female", pitch=3, speed=3, idempotency_key=None, output_file=None):
        """
        使用默认参考音频生成语音
        
        Args:
            text (str): 要合成的文本
            gender (str): 性别 ("male" 或 "female")
            pitch (int): 音调 (1-5)
            speed (int): 语速 (1-5)
            idempotency_key (str, optional): 幂等性键
            output_file (str, optional): 输出文件路径
        
        Returns:
            bool: 是否成功
            str: 成功时返回文件路径，失败时返回错误信息
        """
        data = {
            "text": text,
            "gender": gender,
            "pitch": pitch,
            "speed": speed
        }
        
        if idempotency_key:
            data["idempotency_key"] = idempotency_key
        
        try:
            response = requests.post(f"{self.base_url}/tts/create", data=data)
            
            if response.status_code == 200:
                if output_file is None:
                    output_file = f"output_{int(time.time())}.wav"
                
                with open(output_file, "wb") as f:
                    f.write(response.content)
                
                return True, output_file
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
    
    def clone_voice(self, text, prompt_audio_path, prompt_text=None, 
                   gender=None, pitch=None, speed=None, idempotency_key=None, output_file=None):
        """
        使用参考音频克隆语音
        
        Args:
            text (str): 要合成的文本
            prompt_audio_path (str): 参考音频文件路径
            prompt_text (str, optional): 参考音频的文本内容
            gender (str, optional): 性别
            pitch (int, optional): 音调
            speed (int, optional): 语速
            idempotency_key (str, optional): 幂等性键
            output_file (str, optional): 输出文件路径
        
        Returns:
            bool: 是否成功
            str: 成功时返回文件路径，失败时返回错误信息
        """
        if not os.path.exists(prompt_audio_path):
            return False, f"参考音频文件不存在: {prompt_audio_path}"
        
        data = {"text": text}
        
        if prompt_text:
            data["prompt_text"] = prompt_text
        if gender:
            data["gender"] = gender
        if pitch:
            data["pitch"] = pitch
        if speed:
            data["speed"] = speed
        if idempotency_key:
            data["idempotency_key"] = idempotency_key
        
        files = {
            "prompt_audio": (os.path.basename(prompt_audio_path), 
                           open(prompt_audio_path, "rb"), "audio/wav")
        }
        
        try:
            response = requests.post(f"{self.base_url}/tts/clone", data=data, files=files)
            
            if response.status_code == 200:
                if output_file is None:
                    output_file = f"cloned_{int(time.time())}.wav"
                
                with open(output_file, "wb") as f:
                    f.write(response.content)
                
                return True, output_file
            else:
                return False, f"HTTP {response.status_code}: {response.text}"
        except Exception as e:
            return False, str(e)
        finally:
            files["prompt_audio"][1].close()


def main():
    """主函数 - 演示如何使用客户端"""
    client = IndexTTSClient()
    
    print("IndexTTS API 客户端示例")
    print("=" * 40)
    
    # 1. 检查服务状态
    print("1. 检查服务状态...")
    is_healthy, result = client.health_check()
    if is_healthy:
        print(f"✓ 服务正常: {result}")
    else:
        print(f"✗ 服务异常: {result}")
        return
    
    # 2. 测试语音合成
    print("\n2. 测试语音合成...")
    text = "大家好，我是IndexTTS API客户端示例。今天天气不错。"
    success, result = client.create_tts(text, gender="female", pitch=3, speed=3)
    if success:
        print(f"✓ 语音合成成功: {result}")
    else:
        print(f"✗ 语音合成失败: {result}")
    
    # 3. 测试语音克隆
    print("\n3. 测试语音克隆...")
    prompt_audio = "tests/sample_prompt.wav"
    if os.path.exists(prompt_audio):
        clone_text = "这是语音克隆测试。我正在使用IndexTTS的API服务。"
        success, result = client.clone_voice(
            text=clone_text,
            prompt_audio_path=prompt_audio,
            prompt_text="这是参考音频。"
        )
        if success:
            print(f"✓ 语音克隆成功: {result}")
        else:
            print(f"✗ 语音克隆失败: {result}")
    else:
        print(f"✗ 找不到参考音频文件: {prompt_audio}")
    
    print("\n演示完成！")


if __name__ == "__main__":
    main() 