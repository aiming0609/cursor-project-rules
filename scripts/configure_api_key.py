#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 帮助用户配置API密钥的辅助脚本
"""

import os
import json
import logging
from pathlib import Path
import subprocess
import sys

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
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

def update_vscode_settings(api_key):
    """更新VSCode设置文件"""
    settings_path = find_vscode_settings()
    if not settings_path:
        logger.error("无法找到VSCode设置文件")
        return False
    
    try:
        # 读取现有设置
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
        
        # 更新API密钥设置
        settings["cursor-rules.apiKey"] = api_key
        
        # 写回设置文件
        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        logger.info(f"已成功更新API密钥设置")
        return True
    except Exception as e:
        logger.error(f"更新设置时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n===== Cursor Project Rules API密钥配置助手 =====\n")
    
    # 获取API密钥
    api_key = input("请输入您的API密钥: ").strip()
    if not api_key:
        print("API密钥不能为空")
        return
    
    # 更新设置
    if update_vscode_settings(api_key):
        print("\n[√] API密钥已成功配置")
        print("\n现在您可以在VSCode中运行扩展，不会再收到配置提示")
    else:
        print("\n[!] API密钥配置失败")
        print("\n您可以手动配置API密钥:")
        print("1. 在VSCode中打开设置 (Ctrl+,)")
        print("2. 搜索 'cursor-rules.apiKey'")
        print("3. 输入您的API密钥")

if __name__ == "__main__":
    main() 