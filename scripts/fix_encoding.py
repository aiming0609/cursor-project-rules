#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 修复Windows控制台编码问题
"""

import os
import sys
import ctypes
import subprocess
import logging
from pathlib import Path

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)

def set_windows_console_utf8():
    """设置Windows控制台为UTF-8编码"""
    if sys.platform != 'win32':
        logger.info("非Windows系统，无需修复编码")
        return True
        
    try:
        # 尝试使用SetConsoleOutputCP函数设置控制台代码页
        kernel32 = ctypes.WinDLL('kernel32')
        result = kernel32.SetConsoleOutputCP(65001)  # 65001是UTF-8的代码页
        
        if result == 0:
            logger.error("设置控制台代码页失败")
            return False
            
        # 检查是否设置成功
        current_cp = kernel32.GetConsoleOutputCP()
        if current_cp != 65001:
            logger.error(f"设置控制台代码页不正确，当前为: {current_cp}")
            return False
            
        logger.info("成功设置控制台代码页为UTF-8 (65001)")
        return True
    except Exception as e:
        logger.error(f"设置控制台代码页时出错: {str(e)}")
        return False

def fix_fetch_script():
    """修复fetch_and_convert.py脚本中的编码问题"""
    script_path = Path(__file__).parent / 'fetch_and_convert.py'
    
    if not script_path.exists():
        logger.error(f"找不到脚本文件: {script_path}")
        return False
        
    try:
        # 读取脚本内容
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 检查是否已经包含编码修复代码
        if "codecs.getwriter('utf-8')" in content:
            logger.info("脚本已包含编码修复代码")
            return True
            
        # 添加编码修复代码
        import_line = "import sys"
        encode_fix = """
# 设置控制台编码，避免乱码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)
"""
        # 替换内容
        new_content = content.replace(import_line, import_line + encode_fix)
        
        # 写回文件
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
            
        logger.info(f"成功修复脚本文件: {script_path}")
        return True
    except Exception as e:
        logger.error(f"修复脚本时出错: {str(e)}")
        return False

def test_encoding():
    """测试中文显示"""
    try:
        # 测试中文输出
        test_text = "测试中文字符: 你好，世界！"
        print(test_text)
        logger.info(test_text)
        
        # 测试emoji表情
        emoji_text = "测试表情符号: 😊 🎉 🚀"
        print(emoji_text)
        logger.info(emoji_text)
        
        return True
    except Exception as e:
        logger.error(f"测试编码时出错: {str(e)}")
        return False

def main():
    """主函数"""
    print("\n===== Windows控制台编码修复工具 =====\n")
    
    # 设置控制台编码
    print("1. 设置Windows控制台为UTF-8编码...")
    if set_windows_console_utf8():
        print("  [√] 成功设置控制台编码")
    else:
        print("  [!] 设置控制台编码失败")
        print("      请尝试手动运行: chcp 65001")
    
    # 修复脚本
    print("\n2. 修复脚本编码问题...")
    if fix_fetch_script():
        print("  [√] 成功修复脚本")
    else:
        print("  [!] 修复脚本失败")
    
    # 测试编码
    print("\n3. 测试中文字符显示...")
    if test_encoding():
        print("  [√] 中文字符显示正常")
    else:
        print("  [!] 中文字符显示异常")
    
    print("\n===== 修复完成 =====")
    print("\n请尝试重新运行扩展，查看是否解决了乱码问题")
    print("如果还有问题，请尝试在命令行中运行以下命令后再测试:")
    print("  chcp 65001")

if __name__ == "__main__":
    main() 