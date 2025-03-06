#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description AI模型配置助手，帮助用户配置和管理AI模型参数
"""

import os
import sys
import argparse

# 设置控制台编码，避免乱码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 导入配置管理模块
try:
    from config import get_model_config, save_config, load_config
except ImportError:
    # 如果无法直接导入，尝试从scripts目录导入
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import get_model_config, save_config, load_config

def configure_model():
    """配置AI模型参数"""
    print("============== Cursor规则生成器 - AI模型配置助手 ==============")
    print("此助手将帮助您配置用于生成和定制规则的AI模型参数。")
    print("您的配置将被保存，以便在未来使用时无需重复输入。")
    print("您也可以随时使用此工具更新配置。")
    print("==============================================================")
    print()
    
    # 强制提示用户输入配置（即使已有配置）
    config = get_model_config(force_prompt=True)
    
    print("\n配置已保存！您现在可以使用本地规则选择器了。")
    
    # 显示配置信息
    print("\n当前配置信息:")
    print(f"模型URL: {config.get('model_url')}")
    print(f"API密钥: {'*' * 8 + config.get('api_key')[-4:] if config.get('api_key') else '未设置'}")
    print(f"模型名称: {config.get('model_name')}")
    
    # 返回配置信息
    return config

def test_model_connection(config):
    """测试与AI模型的连接"""
    import requests
    import json
    
    print("\n正在测试与AI模型的连接...")
    
    model_url = config.get('model_url')
    api_key = config.get('api_key')
    model_name = config.get('model_name')
    
    if not all([model_url, api_key, model_name]):
        print("错误: 配置不完整，无法测试连接")
        return False
    
    try:
        # 构建简单测试请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Say hello"}
            ],
            "temperature": 0.5,
            "max_tokens": 20
        }
        
        # 发送请求
        response = requests.post(model_url, headers=headers, json=data, timeout=10)
        
        # 检查响应
        if response.status_code == 200:
            print("连接测试成功！AI模型配置有效。")
            return True
        else:
            print(f"连接测试失败: 状态码 {response.status_code}")
            print(f"错误信息: {response.text}")
            return False
            
    except Exception as e:
        print(f"连接测试失败: {str(e)}")
        return False

def show_current_config():
    """显示当前配置"""
    config = load_config()
    
    print("\n当前AI模型配置:")
    print(f"模型URL: {config.get('model_url') or '未设置'}")
    print(f"API密钥: {'*' * 8 + config.get('api_key')[-4:] if config.get('api_key') else '未设置'}")
    print(f"模型名称: {config.get('model_name') or '未设置'}")
    print(f"默认使用AI: {'是' if config.get('use_ai', True) else '否'}")
    
    # 检查配置是否完整
    if all([config.get('model_url'), config.get('api_key'), config.get('model_name')]):
        print("\n配置状态: 完整")
    else:
        print("\n配置状态: 不完整")
        missing = []
        if not config.get('model_url'):
            missing.append("模型URL")
        if not config.get('api_key'):
            missing.append("API密钥")
        if not config.get('model_name'):
            missing.append("模型名称")
        
        print(f"缺少的配置项: {', '.join(missing)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Cursor规则生成器 - AI模型配置助手')
    parser.add_argument('--test', action='store_true', help='测试与AI模型的连接')
    parser.add_argument('--show', action='store_true', help='显示当前配置')
    args = parser.parse_args()
    
    if args.show:
        show_current_config()
        return
    
    # 配置模型参数
    config = configure_model()
    
    # 如果指定了测试选项，测试与模型的连接
    if args.test:
        test_model_connection(config)

if __name__ == "__main__":
    main() 