#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 模拟VSCode扩展功能，测试规则生成和二进制写入
"""

import os
import sys
import json
import logging
from pathlib import Path
import subprocess

# 设置控制台编码，避免乱码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def simulate_extension():
    """模拟VSCode扩展的功能"""
    logger.info("模拟VSCode扩展功能开始...")
    
    # 1. 模拟获取工作区路径
    workspace_path = os.getcwd()
    logger.info(f"工作区路径: {workspace_path}")
    
    # 2. 模拟获取配置
    model_url = "https://api.example.com/v1/chat/completions"
    api_key = "sample_api_key_for_testing"
    model_name = "test-model"
    
    logger.info(f"使用模型配置: URL={model_url}, 模型={model_name}")
    
    # 3. 模拟生成规则命令
    logger.info("执行规则生成命令...")
    
    # 检查是否需要跳过网络错误
    ignore_network = os.environ.get('IGNORE_NETWORK_ERRORS', '0').lower() in ('1', 'true', 'yes')
    use_sample_rules = os.environ.get('USE_SAMPLE_RULES', '0').lower() in ('1', 'true', 'yes')
    
    # 调用fetch_and_convert.py脚本
    try:
        fetch_script_path = os.path.join("scripts", "fetch_and_convert.py")
        args = [
            sys.executable,
            fetch_script_path,
            workspace_path,
            "--model-url", model_url,
            "--api-key", api_key,
            "--model-name", model_name
        ]
        
        # 如果需要跳过网络错误，添加环境变量
        env = os.environ.copy()
        if ignore_network or use_sample_rules:
            env['USE_SAMPLE_RULES'] = '1'
            args.append('--use-samples')
            logger.info("已启用样例规则模式，将跳过网络错误")
        
        logger.info(f"执行命令: {' '.join(args)}")
        
        # 执行命令并捕获输出
        process = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            env=env
        )
        
        stdout, stderr = process.communicate()
        
        if stdout:
            logger.info(f"标准输出:\n{stdout}")
        
        if stderr:
            logger.error(f"标准错误:\n{stderr}")
            
        if process.returncode != 0:
            logger.error(f"命令执行失败，返回码: {process.returncode}")
            
            # 如果启用了样例规则模式但仍然失败，尝试直接生成样例规则
            if use_sample_rules:
                logger.info("尝试直接生成样例规则...")
            else:
                logger.warning("如果遇到网络错误，请尝试设置环境变量IGNORE_NETWORK_ERRORS=1")
        else:
            logger.info("命令执行成功")
        
    except Exception as e:
        logger.error(f"执行命令时出错: {str(e)}")
    
    # 4. 模拟生成示例规则
    logger.info("生成示例规则...")
    test_script_path = os.path.join("scripts", "test_binary_write.py")
    try:
        subprocess.run([sys.executable, test_script_path], check=True)
        logger.info("示例规则生成成功")
    except subprocess.CalledProcessError as e:
        logger.error(f"生成示例规则失败: {str(e)}")
    
    # 5. 验证生成的规则文件
    rules_dir = Path(workspace_path) / '.cursor' / 'rules'
    
    if rules_dir.exists():
        logger.info(f"规则目录已创建: {rules_dir}")
        
        # 列出规则文件
        rules_files = list(rules_dir.glob('*.mdc'))
        if rules_files:
            logger.info(f"找到 {len(rules_files)} 个规则文件:")
            for rule_file in rules_files:
                logger.info(f"- {rule_file.name} ({rule_file.stat().st_size} 字节)")
                
                # 查看文件是否正确（以二进制方式读取）
                with open(rule_file, 'rb') as f:
                    content = f.read()
                    logger.info(f"  内容前100字节: {content[:100]}")
        else:
            logger.warning("未找到规则文件")
    else:
        logger.error(f"规则目录未创建: {rules_dir}")
    
    logger.info("模拟VSCode扩展功能结束")

if __name__ == "__main__":
    simulate_extension() 