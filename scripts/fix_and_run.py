#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 修复VSCode扩展启动问题并运行扩展
"""

import os
import sys
import json
import logging
from pathlib import Path
import subprocess

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fix_launch_config():
    """修复启动配置"""
    try:
        # 获取工作区路径
        workspace_path = os.getcwd()
        logger.info(f"工作区路径: {workspace_path}")
        
        # 创建.vscode目录（如果不存在）
        vscode_dir = Path(workspace_path) / '.vscode'
        vscode_dir.mkdir(parents=True, exist_ok=True)
        
        # 创建或修改launch.json
        launch_path = vscode_dir / 'launch.json'
        
        # 创建新的launch.json内容
        launch_config = {
            "version": "0.2.0",
            "configurations": [
                {
                    "name": "运行扩展",
                    "type": "extensionHost",
                    "request": "launch",
                    "args": [
                        "--extensionDevelopmentPath=${workspaceFolder}",
                        "--disable-extensions"
                    ],
                    "outFiles": [
                        "${workspaceFolder}/extension/out/**/*.js"
                    ],
                    "preLaunchTask": "${defaultBuildTask}"
                }
            ]
        }
        
        # 写入文件
        with open(launch_path, 'w', encoding='utf-8') as f:
            json.dump(launch_config, f, ensure_ascii=False, indent=2)
            
        logger.info(f"已创建启动配置文件: {launch_path}")
        
        return True
    except Exception as e:
        logger.error(f"修复启动配置时出错: {str(e)}")
        return False

def run_extension_simulation():
    """运行扩展模拟"""
    try:
        # 首先检查是否已编译TypeScript
        out_dir = Path('.') / 'extension' / 'out'
        if not out_dir.exists() or not list(out_dir.glob('**/*.js')):
            logger.warning("没有找到编译后的JS文件，尝试编译TypeScript...")
            subprocess.run(['npm', 'run', 'compile'], check=True)
        
        # 运行模拟脚本
        logger.info("运行扩展模拟脚本...")
        simulate_path = Path('.') / 'scripts' / 'simulate_extension.py'
        
        if not simulate_path.exists():
            logger.error(f"模拟脚本不存在: {simulate_path}")
            return False
            
        subprocess.run([sys.executable, str(simulate_path)], check=True)
        
        logger.info("扩展模拟完成")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"运行命令时出错: {str(e)}")
        return False
    except Exception as e:
        logger.error(f"运行扩展模拟时出错: {str(e)}")
        return False

def show_help():
    """显示帮助信息"""
    print("\n解决方案：")
    print("1. 运行VSCode并安装Markdown扩展（最简单的方法）")
    print("   - 在弹出的对话框中点击'查找 Markdown 扩展'按钮")
    print("   - 安装官方的Markdown扩展")
    print("\n2. 禁用扩展")
    print("   - 启动VSCode时添加 --disable-extensions 参数")
    print("   - 我们已经自动修改了launch.json加入这个参数")
    print("\n3. 使用模拟脚本验证功能:")
    print("   - 运行: python scripts/simulate_extension.py")
    print("   - 这将测试规则生成和二进制写入功能")

def main():
    """主函数"""
    print("\n===== Cursor Project Rules Generator 启动助手 =====\n")
    print("您在尝试运行VSCode扩展时遇到了问题: '没有用于查看 Markdown 的扩展'\n")
    
    # 第一步：修复启动配置
    print("步骤1: 修复启动配置...")
    if not fix_launch_config():
        print("  [!] 无法修复启动配置")
    else:
        print("  [√] 启动配置已修复")
    
    # 第二步：运行扩展模拟
    print("\n步骤2: 运行扩展模拟...")
    if not run_extension_simulation():
        print("  [!] 扩展模拟失败")
    else:
        print("  [√] 扩展模拟成功")
    
    # 显示帮助信息
    print("\n===== 解决方案 =====")
    show_help()

if __name__ == "__main__":
    main() 