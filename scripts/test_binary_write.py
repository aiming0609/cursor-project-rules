#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 测试二进制写入功能
"""

import os
import logging
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# MDC模板
MDC_TEMPLATE = """---
name: {name}.mdc
description: {description}
globs: {globs}
---

{content}
"""

def main():
    """测试二进制写入MDC文件"""
    # 创建.cursor/rules目录
    rules_dir = Path('.') / '.cursor' / 'rules'
    rules_dir.mkdir(parents=True, exist_ok=True)
    
    # 创建一个测试规则
    name = "test-binary-write"
    description = "测试二进制写入功能"
    globs = "**/*.{ts,tsx,js,jsx}"
    content = "- 这是测试规则1\n- 这是测试规则2\n- 这是包含中文的测试规则"
    
    # 创建MDC文件内容
    mdc_content = MDC_TEMPLATE.format(
        name=name,
        description=description,
        globs=globs,
        content=content
    )
    
    # 使用二进制模式写入文件
    file_path = rules_dir / f"{name}.mdc"
    logger.info(f"正在使用二进制模式写入文件: {file_path}")
    with open(file_path, 'wb') as f:
        f.write(mdc_content.encode('utf-8'))
        
    logger.info(f"文件写入成功: {file_path}")
    
    # 读取文件内容进行验证
    logger.info(f"使用二进制模式读取文件内容进行验证")
    with open(file_path, 'rb') as f:
        binary_content = f.read()
        
    logger.info(f"文件大小: {len(binary_content)} 字节")
    logger.info(f"文件内容(前100字节): {binary_content[:100]}")
    
    # 使用文本模式读取进行对比
    with open(file_path, 'r', encoding='utf-8') as f:
        text_content = f.read()
        
    logger.info(f"文本模式读取的内容长度: {len(text_content)} 字符")
    logger.info(f"内容一致性检查: {'成功' if text_content == mdc_content else '失败'}")

if __name__ == "__main__":
    main() 