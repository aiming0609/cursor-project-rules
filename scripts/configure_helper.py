#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description Cursor项目规则生成器配置助手脚本
"""

import os
import json
import logging
import argparse
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8' if hasattr(logging, 'ENCODING') else None  # 兼容Python 3.8以下版本
)
logger = logging.getLogger(__name__)

def find_vscode_settings():
    """查找VSCode设置文件"""
    # 尝试查找用户设置文件
    home_dir = Path.home()
    
    # Windows路径
    win_path = home_dir / "AppData" / "Roaming" / "Code" / "User" / "settings.json"
    # Linux路径
    linux_path = home_dir / ".config" / "Code" / "User" / "settings.json"
    # macOS路径
    mac_path = home_dir / "Library" / "Application Support" / "Code" / "User" / "settings.json"
    
    if win_path.exists():
        return win_path
    elif linux_path.exists():
        return linux_path
    elif mac_path.exists():
        return mac_path
    else:
        return None

def update_vscode_settings(model_url=None, api_key=None, model_name=None):
    """更新VSCode设置文件"""
    settings_path = find_vscode_settings()
    if not settings_path:
        logger.error("无法找到VSCode设置文件")
        return False
    
    try:
        # 读取现有设置
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 更新设置
        if model_url:
            settings["cursor-rules.modelUrl"] = model_url
            logger.info(f"已设置模型URL: {model_url}")
            
        if api_key:
            settings["cursor-rules.apiKey"] = api_key
            logger.info(f"已设置API密钥: {'*' * 8}")
            
        if model_name:
            settings["cursor-rules.modelName"] = model_name
            logger.info(f"已设置模型名称: {model_name}")
        
        # 写回设置文件
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        logger.info(f"设置已成功更新")
        return True
    except Exception as e:
        logger.error(f"更新设置时出错: {str(e)}")
        return False

def get_from_env_or_input(env_var, prompt, sensitive=False):
    """从环境变量或用户输入获取值"""
    value = os.environ.get(env_var)
    if value:
        return value
    
    if sensitive:
        # 提示用户输入敏感信息（例如API密钥）
        import getpass
        return getpass.getpass(prompt)
    else:
        return input(prompt)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='Cursor项目规则生成器配置助手')
    parser.add_argument('--batch', action='store_true', help='批处理模式，从环境变量读取设置')
    args = parser.parse_args()
    
    print("\n===== Cursor项目规则生成器配置助手 =====\n")
    
    if args.batch:
        # 批处理模式，从环境变量读取
        model_url = os.environ.get('CURSOR_RULES_MODEL_URL')
        api_key = os.environ.get('CURSOR_RULES_API_KEY')
        model_name = os.environ.get('CURSOR_RULES_MODEL_NAME')
        
        if not any([model_url, api_key, model_name]):
            logger.error("批处理模式下未找到任何环境变量设置")
            logger.info("请设置以下环境变量之一或多个:")
            logger.info("- CURSOR_RULES_MODEL_URL: 模型API的URL地址")
            logger.info("- CURSOR_RULES_API_KEY: 模型的API密钥")
            logger.info("- CURSOR_RULES_MODEL_NAME: 使用的模型名称")
            return
    else:
        # 交互模式
        print("请配置Cursor项目规则生成器所需的设置:\n")
        
        # 获取模型URL
        model_url = get_from_env_or_input(
            'CURSOR_RULES_MODEL_URL',
            "1. 请输入模型API的URL地址 (例如: https://api.openai.com/v1/chat/completions): "
        )
        
        # 获取API密钥
        api_key = get_from_env_or_input(
            'CURSOR_RULES_API_KEY',
            "2. 请输入模型的API密钥: ",
            sensitive=True
        )
        
        # 获取模型名称
        model_name = get_from_env_or_input(
            'CURSOR_RULES_MODEL_NAME',
            "3. 请输入使用的模型名称 (例如: gpt-3.5-turbo): "
        )
    
    # 确认用户输入
    print("\n您将更新以下设置:")
    if model_url:
        print(f"- 模型URL: {model_url}")
    if api_key:
        print(f"- API密钥: {'*' * 8}")
    if model_name:
        print(f"- 模型名称: {model_name}")
    
    # 更新设置
    if not args.batch:
        confirm = input("\n确认更新这些设置? (y/n): ").lower()
        if confirm != 'y':
            print("已取消更新设置")
            return
    
    if update_vscode_settings(model_url, api_key, model_name):
        print("\n[√] 设置已成功更新")
        print("\n现在您可以在VSCode中使用Cursor项目规则生成器功能")
    else:
        print("\n[!] 设置更新失败")
        print("\n您可以手动配置设置:")
        print("1. 在VSCode中打开设置 (Ctrl+,)")
        print("2. 搜索 'cursor-rules'")
        print("3. 输入相应的设置值")

if __name__ == "__main__":
    main() 