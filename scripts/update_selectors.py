#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 更新主抓取脚本中的CSS选择器
"""

import os
import sys
import re
import json
import argparse
from pathlib import Path

# 设置控制台编码，避免乱码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

def load_selectors_config(config_file='selectors.json'):
    """加载选择器配置文件，如果不存在则创建默认配置"""
    if not os.path.exists(config_file):
        # 默认选择器配置
        default_config = {
            "card_selector": ".rule-card",
            "title_selector": ".rule-title",
            "description_selector": ".rule-description",
            "content_selector": ".rule-content",
            "glob_selector": ".rule-glob",
            "author_selector": ".rule-author"
        }
        
        # 保存默认配置
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
        
        print(f"已创建默认选择器配置文件: {config_file}")
        return default_config
    
    # 加载现有配置
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        print(f"已加载选择器配置: {config_file}")
        return config
    except Exception as e:
        print(f"加载配置文件时出错: {str(e)}")
        return None

def update_fetch_script(script_path, selectors):
    """更新主抓取脚本中的选择器"""
    if not os.path.exists(script_path):
        print(f"错误: 找不到脚本文件 {script_path}")
        return False
    
    try:
        # 读取脚本内容
        with open(script_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 备份原始文件
        backup_path = f"{script_path}.backup"
        with open(backup_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"已备份原始文件到: {backup_path}")
        
        # 更新选择器
        for selector_name, selector_value in selectors.items():
            # 构建正则表达式模式
            base_name = selector_name.replace('_selector', '')
            patterns = [
                # 直接选择器赋值
                rf"({base_name}_elem = card\.select_one\()'\.{base_name}'",
                rf"({base_name}_elem = card\.select_one\()'\.\w+-{base_name}'",
                rf"({base_name}_elem = card\.select_one\()'{selector_name}'",
                # 变量声明
                rf"({selector_name} = )'\.{base_name}'",
                rf"({selector_name} = )'\.rule-{base_name}'",
                # 直接字符串使用
                rf"(\.select_one\()'\.\w+-{base_name}'",
                rf"(\.select_one\()'\.{base_name}'"
            ]
            
            # 应用替换
            for pattern in patterns:
                content = re.sub(pattern, f"\\1'{selector_value}'", content)
        
        # 写回修改后的内容
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"已更新脚本 {script_path} 中的选择器")
        return True
    except Exception as e:
        print(f"更新脚本时出错: {str(e)}")
        return False

def update_all_scripts(selectors, scripts_dir='scripts'):
    """更新所有相关脚本中的选择器"""
    # 查找需要更新的脚本
    scripts_to_update = [
        os.path.join(scripts_dir, 'fetch_and_convert.py')
    ]
    
    # 尝试更新所有脚本
    success = True
    for script in scripts_to_update:
        if os.path.exists(script):
            if update_fetch_script(script, selectors):
                print(f"✓ 已成功更新 {script}")
            else:
                print(f"✗ 更新 {script} 失败")
                success = False
        else:
            print(f"! 脚本 {script} 不存在，已跳过")
    
    return success

def interactive_update():
    """交互式更新选择器"""
    print("\n===== 交互式更新CSS选择器 =====\n")
    
    # 加载当前配置
    current_selectors = load_selectors_config()
    if not current_selectors:
        print("无法加载选择器配置，无法继续")
        return False
    
    # 显示当前配置
    print("\n当前选择器配置:")
    for name, value in current_selectors.items():
        print(f"- {name}: {value}")
    
    # 询问是否要更新
    update_choice = input("\n是否要更新选择器? (y/n): ").lower()
    if update_choice != 'y':
        print("已取消更新")
        return False
    
    # 交互式更新每个选择器
    new_selectors = current_selectors.copy()
    print("\n请输入新的选择器值 (直接按Enter保持不变):")
    
    for name, current_value in current_selectors.items():
        new_value = input(f"{name} [{current_value}]: ").strip()
        if new_value:
            new_selectors[name] = new_value
    
    # 显示更新后的配置
    print("\n更新后的选择器配置:")
    for name, value in new_selectors.items():
        changed = value != current_selectors[name]
        print(f"- {name}: {value} {'(已更新)' if changed else ''}")
    
    # 确认更新
    confirm = input("\n确认更新主脚本中的选择器? (y/n): ").lower()
    if confirm != 'y':
        print("已取消更新")
        return False
    
    # 保存新配置
    try:
        with open('selectors.json', 'w', encoding='utf-8') as f:
            json.dump(new_selectors, f, ensure_ascii=False, indent=2)
        print("已保存新的选择器配置")
    except Exception as e:
        print(f"保存配置时出错: {str(e)}")
        return False
    
    # 更新脚本
    return update_all_scripts(new_selectors)

def json_file_update(json_file):
    """从JSON文件更新选择器"""
    if not os.path.exists(json_file):
        print(f"错误: 找不到JSON文件 {json_file}")
        return False
    
    try:
        # 加载JSON文件
        with open(json_file, 'r', encoding='utf-8') as f:
            new_selectors = json.load(f)
        
        print(f"已加载选择器从文件: {json_file}")
        print("\n选择器配置:")
        for name, value in new_selectors.items():
            print(f"- {name}: {value}")
        
        # 确认更新
        confirm = input("\n确认更新主脚本中的选择器? (y/n): ").lower()
        if confirm != 'y':
            print("已取消更新")
            return False
        
        # 保存为默认配置
        with open('selectors.json', 'w', encoding='utf-8') as f:
            json.dump(new_selectors, f, ensure_ascii=False, indent=2)
        print("已保存为默认选择器配置")
        
        # 更新脚本
        return update_all_scripts(new_selectors)
    except Exception as e:
        print(f"处理JSON文件时出错: {str(e)}")
        return False

def show_help():
    """显示帮助信息"""
    print("""
====== CSS选择器更新工具 ======

此工具用于更新主抓取脚本中的CSS选择器，以适应网站结构变化。

使用方法:
1. 交互式更新 (默认):
   python update_selectors.py

2. 从JSON文件更新:
   python update_selectors.py --json selectors.json

3. 显示帮助:
   python update_selectors.py --help

建议流程:
1. 首先使用 test_fetch_interactive.py 探索网站并找到有效的选择器
2. 记录有效的选择器
3. 使用此工具更新主脚本中的选择器
4. 测试更新后的脚本是否能正确获取规则

当前支持的选择器:
- card_selector: 规则卡片的选择器
- title_selector: 规则标题的选择器
- description_selector: 规则描述的选择器
- content_selector: 规则内容的选择器
- glob_selector: 文件匹配模式的选择器
- author_selector: 作者信息的选择器
""")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='更新主抓取脚本中的CSS选择器')
    parser.add_argument('--json', '-j', help='从JSON文件加载选择器配置')
    parser.add_argument('--help-more', '-hm', action='store_true', help='显示更多帮助信息')
    args = parser.parse_args()
    
    if args.help_more:
        show_help()
        return
    
    if args.json:
        # 从JSON文件更新
        success = json_file_update(args.json)
    else:
        # 交互式更新
        success = interactive_update()
    
    if success:
        print("\n✓ 已成功更新选择器!")
    else:
        print("\n✗ 更新选择器失败!")

if __name__ == "__main__":
    main() 