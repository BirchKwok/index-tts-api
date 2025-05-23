#!/usr/bin/env python3
"""
IndexTTS API 语速和音调控制演示脚本
"""

import requests
import os

def test_speed_control():
    """测试语速控制功能"""
    print("🎵 测试语速控制功能")
    print("=" * 40)
    
    speed_tests = [
        {"speed": 1, "text": "这是最慢的语速，每个字都说得很清楚。", "name": "最慢语速"},
        {"speed": 2, "text": "这是较慢的语速，比较从容不迫。", "name": "较慢语速"},
        {"speed": 3, "text": "这是正常的语速，听起来很自然。", "name": "正常语速"},
        {"speed": 4, "text": "这是较快的语速，显得比较急切。", "name": "较快语速"},
        {"speed": 5, "text": "这是最快的语速，说话非常迅速。", "name": "最快语速"},
    ]
    
    for test in speed_tests:
        print(f"  正在生成: {test['name']} (speed={test['speed']})")
        
        data = {
            "text": test["text"],
            "gender": "female",
            "pitch": 3,  # 固定正常音调
            "speed": test["speed"],
            "idempotency_key": f"speed_demo_{test['speed']}"
        }
        
        try:
            response = requests.post("http://localhost:8080/tts/create", data=data, timeout=30)
            if response.status_code == 200:
                filename = f"demo_speed_{test['speed']}_{test['name']}.wav"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"    ✓ 已保存到: {filename}")
            else:
                print(f"    ✗ 生成失败: {response.status_code}")
        except Exception as e:
            print(f"    ✗ 请求失败: {e}")
    
    print()

def test_pitch_control():
    """测试音调控制功能"""
    print("🎹 测试音调控制功能")
    print("=" * 40)
    
    pitch_tests = [
        {"pitch": 1, "text": "这是最低的音调，声音听起来比较低沉。", "name": "最低音调"},
        {"pitch": 2, "text": "这是较低的音调，声音稍微低一些。", "name": "较低音调"},
        {"pitch": 3, "text": "这是正常的音调，听起来很自然。", "name": "正常音调"},
        {"pitch": 4, "text": "这是较高的音调，声音稍微高一些。", "name": "较高音调"},
        {"pitch": 5, "text": "这是最高的音调，声音听起来比较清亮。", "name": "最高音调"},
    ]
    
    for test in pitch_tests:
        print(f"  正在生成: {test['name']} (pitch={test['pitch']})")
        
        data = {
            "text": test["text"],
            "gender": "female",
            "pitch": test["pitch"],
            "speed": 3,  # 固定正常语速
            "idempotency_key": f"pitch_demo_{test['pitch']}"
        }
        
        try:
            response = requests.post("http://localhost:8080/tts/create", data=data, timeout=30)
            if response.status_code == 200:
                filename = f"demo_pitch_{test['pitch']}_{test['name']}.wav"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"    ✓ 已保存到: {filename}")
            else:
                print(f"    ✗ 生成失败: {response.status_code}")
        except Exception as e:
            print(f"    ✗ 请求失败: {e}")
    
    print()

def test_combinations():
    """测试语速和音调组合"""
    print("🎭 测试语速和音调组合")
    print("=" * 40)
    
    combination_tests = [
        {"speed": 1, "pitch": 1, "text": "慢速低音：深沉而从容的声音。", "name": "慢速低音"},
        {"speed": 3, "pitch": 3, "text": "正常组合：自然平衡的声音。", "name": "标准组合"},
        {"speed": 5, "pitch": 5, "text": "快速高音：活泼明快的声音。", "name": "快速高音"},
        {"speed": 1, "pitch": 5, "text": "慢速高音：清亮而优雅的声音。", "name": "慢速高音"},
        {"speed": 5, "pitch": 1, "text": "快速低音：急促而有力的声音。", "name": "快速低音"},
    ]
    
    for test in combination_tests:
        print(f"  正在生成: {test['name']} (speed={test['speed']}, pitch={test['pitch']})")
        
        data = {
            "text": test["text"],
            "gender": "female",
            "pitch": test["pitch"],
            "speed": test["speed"],
            "idempotency_key": f"combo_demo_{test['speed']}_{test['pitch']}"
        }
        
        try:
            response = requests.post("http://localhost:8080/tts/create", data=data, timeout=30)
            if response.status_code == 200:
                filename = f"demo_combo_{test['speed']}_{test['pitch']}_{test['name']}.wav"
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f"    ✓ 已保存到: {filename}")
            else:
                print(f"    ✗ 生成失败: {response.status_code}")
        except Exception as e:
            print(f"    ✗ 请求失败: {e}")

def main():
    """主函数"""
    print("IndexTTS API 语速和音调控制演示")
    print("=" * 50)
    
    # 检查API服务状态
    try:
        response = requests.get("http://localhost:8080/hello", timeout=5)
        if response.status_code == 200:
            print("✓ API服务正常运行")
            print()
        else:
            print("✗ API服务状态异常")
            return
    except Exception as e:
        print("✗ 无法连接到API服务，请确保服务已启动")
        print("  启动命令: python api.py")
        return
    
    # 运行各项测试
    test_speed_control()
    test_pitch_control()
    test_combinations()
    
    print("🎉 演示完成！")
    print("\n生成的音频文件:")
    demo_files = [f for f in os.listdir(".") if f.startswith("demo_") and f.endswith(".wav")]
    for i, file in enumerate(sorted(demo_files), 1):
        print(f"  {i:2d}. {file}")
    
    print(f"\n总共生成了 {len(demo_files)} 个演示音频文件")
    print("您可以播放这些文件来听取语速和音调的差异")

if __name__ == "__main__":
    main() 