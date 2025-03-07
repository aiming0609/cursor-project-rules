#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 配置管理模块，用于存储和加载AI模型配置信息
"""

import os
import json
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8' if hasattr(logging, 'ENCODING') else None  # 兼容Python 3.8以下版本
)
logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".cursor-rules")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")

# 默认配置
DEFAULT_CONFIG = {
    "model_url": "",
    "api_key": "",
    "model_name": "gpt-3.5-turbo",
    "use_ai": True,
    "temperature": 0.5,
    "max_tokens": 2000
}

def load_config():
    """
    加载配置，优先级：环境变量 > 配置文件 > 默认值
    """
    # 初始化配置为默认值
    config = DEFAULT_CONFIG.copy()
    
    # 尝试从配置文件加载
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # 更新配置，但不覆盖默认配置中不存在的键
                for key in config:
                    if key in file_config and file_config[key]:
                        config[key] = file_config[key]
    except Exception as e:
        logger.error(f"加载配置文件失败: {str(e)}")
    
    # 从环境变量加载配置
    env_vars = {
        "model_url": os.environ.get("CURSOR_RULES_MODEL_URL"),
        "api_key": os.environ.get("CURSOR_RULES_API_KEY"),
        "model_name": os.environ.get("CURSOR_RULES_MODEL_NAME"),
        "use_ai": os.environ.get("CURSOR_RULES_USE_AI")
    }
    
    # 更新配置
    for key, value in env_vars.items():
        if value:
            if key == "use_ai":
                # 转换为布尔值
                config[key] = value.lower() in ("yes", "true", "t", "1")
            else:
                config[key] = value
    
    return config

def save_config(config):
    """
    保存配置到文件
    """
    try:
        # 确保配置目录存在
        os.makedirs(CONFIG_DIR, exist_ok=True)
        
        # 保存配置
        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, indent=2)
        
        logger.info(f"配置已保存到: {CONFIG_FILE}")
        return True
    except Exception as e:
        logger.error(f"保存配置失败: {str(e)}")
        return False

def prompt_for_config(config):
    """
    交互式提示用户输入配置信息
    """
    print("\n配置AI模型参数：")
    
    model_url = input(f"模型URL [{config.get('model_url', '')}]: ").strip()
    if model_url:
        config['model_url'] = model_url
    
    api_key = input(f"API密钥 [{config.get('api_key', '')}]: ").strip()
    if api_key:
        config['api_key'] = api_key
    
    model_name = input(f"模型名称 [{config.get('model_name', 'gpt-3.5-turbo')}]: ").strip()
    if model_name:
        config['model_name'] = model_name
    
    # 保存配置
    save_config(config)
    
    return config

def get_model_config(force_prompt=False):
    """
    获取模型配置，如果缺少必要配置项，则提示用户输入
    """
    # 加载配置
    config = load_config()
    
    # 检查是否有必要的配置项
    has_required = all([config.get('model_url'), config.get('api_key'), config.get('model_name')])
    
    # 打印配置检测结果
    logger.info(f"模型配置检测结果: {'完整' if has_required else '不完整'}")
    
    # 强制提示或缺少必要配置项时，提示用户输入
    if force_prompt or not has_required:
        config = prompt_for_config(config)
    
    return config

if __name__ == "__main__":
    # 测试配置加载和保存
    print("当前配置:", load_config())
    
    # 强制提示用户输入配置
    config = get_model_config(force_prompt=True)
    print("更新后的配置:", config) 