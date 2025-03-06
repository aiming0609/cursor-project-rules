#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 从本地JSON文件读取规则并提供选择界面，结合AI大模型定制规则内容
"""

import os
import sys
import json
import logging
import argparse
import requests
import glob
from pathlib import Path
import time

# 导入配置管理模块
try:
    from config import get_model_config, save_config
except ImportError:
    # 如果无法直接导入，尝试从scripts目录导入
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from config import get_model_config, save_config

# 设置控制台编码，避免乱码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8' if hasattr(logging, 'ENCODING') else None  # 兼容Python 3.8以下版本
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

def load_rules_from_json(json_path):
    """从JSON文件加载规则数据"""
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        logger.info(f"成功从 {json_path} 加载了 {len(rules)} 条规则")
        return rules
    except Exception as e:
        logger.error(f"加载规则数据时出错: {str(e)}")
        return []

def display_rules_list(rules):
    """显示规则列表"""
    print("\n===== 可用规则列表 =====\n")
    
    for i, rule in enumerate(rules):
        title = rule.get('title', f"规则 {i+1}")
        tags = ', '.join(rule.get('tags', []))
        print(f"{i+1}. {title}")
        if tags:
            print(f"   标签: {tags}")
        
        # 显示简短描述（取内容的前100个字符）
        content = rule.get('content', '')
        if content:
            short_desc = content.strip()[:100].replace('\n', ' ')
            print(f"   描述: {short_desc}..." if len(content) > 100 else f"   描述: {short_desc}")
        
        print()
    
    return len(rules)

def select_rules(rules, max_rules):
    """让用户选择规则"""
    selected_indices = []
    
    while True:
        try:
            # 提示用户输入
            selection = input("\n请输入要选择的规则编号 (用逗号分隔多个编号，输入'all'选择所有，输入'q'完成选择): ")
            
            # 检查是否退出
            if selection.lower() == 'q':
                break
            
            # 检查是否选择所有
            if selection.lower() == 'all':
                selected_indices = list(range(1, max_rules + 1))
                print(f"已选择所有 {max_rules} 条规则")
                break
            
            # 解析选择的编号
            selected = [int(idx.strip()) for idx in selection.split(',')]
            
            # 验证编号范围
            for idx in selected:
                if idx < 1 or idx > max_rules:
                    print(f"错误: 规则编号 {idx} 超出范围 (1-{max_rules})")
                else:
                    if idx not in selected_indices:
                        selected_indices.append(idx)
            
            # 显示当前选择
            if selected_indices:
                print(f"当前已选择: {', '.join(map(str, selected_indices))}")
        
        except ValueError:
            print("错误: 请输入有效的数字或命令")
        except Exception as e:
            print(f"出错: {str(e)}")
    
    # 返回实际的规则对象（索引转换为0基）
    return [rules[idx - 1] for idx in selected_indices]

def analyze_project_structure(workspace_path):
    """分析项目文件结构，获取项目上下文信息"""
    logger.info(f"分析项目结构: {workspace_path}")
    project_info = {
        "file_types": {},
        "directories": [],
        "technologies": set(),
        "sample_files": []
    }
    
    # 排除目录
    exclude_dirs = ['.git', 'node_modules', '.vscode', '__pycache__', 'venv', 'dist', 'build']
    
    # 遍历项目文件
    for root, dirs, files in os.walk(workspace_path):
        # 排除指定目录
        dirs[:] = [d for d in dirs if d not in exclude_dirs]
        
        # 相对路径
        rel_path = os.path.relpath(root, workspace_path)
        if rel_path != '.' and not any(ex in rel_path for ex in exclude_dirs):
            project_info["directories"].append(rel_path)
        
        # 统计文件类型
        for file in files:
            _, ext = os.path.splitext(file)
            if ext:
                ext = ext.lower()[1:]  # 移除点号并转为小写
                if ext in project_info["file_types"]:
                    project_info["file_types"][ext] += 1
                else:
                    project_info["file_types"][ext] = 1
                    
                # 收集样本文件（每种类型最多3个）
                if ext in ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cs', 'php', 'rb', 'go', 'rs']:
                    file_category = f"{ext}_files"
                    if file_category not in project_info:
                        project_info[file_category] = []
                    
                    if len(project_info[file_category]) < 3:
                        file_path = os.path.join(root, file)
                        try:
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read(2000)  # 读取前2000个字符
                            project_info[file_category].append({
                                "path": os.path.relpath(file_path, workspace_path),
                                "sample": content
                            })
                        except:
                            pass  # 忽略无法读取的文件
    
    # 检测技术栈
    detect_technologies(project_info)
    
    return project_info

def detect_technologies(project_info):
    """基于文件类型和存在的配置文件检测项目使用的技术栈"""
    # 检查文件类型分布
    file_types = project_info["file_types"]
    
    # 前端技术
    if any(ext in file_types for ext in ['jsx', 'tsx']):
        project_info["technologies"].add("React")
    
    if 'vue' in file_types:
        project_info["technologies"].add("Vue.js")
    
    if 'svelte' in file_types:
        project_info["technologies"].add("Svelte")
    
    # 后端技术
    if 'py' in file_types:
        project_info["technologies"].add("Python")
        
    if 'rb' in file_types:
        project_info["technologies"].add("Ruby")
    
    if 'php' in file_types:
        project_info["technologies"].add("PHP")
    
    if 'cs' in file_types:
        project_info["technologies"].add("C#")
    
    if 'java' in file_types:
        project_info["technologies"].add("Java")
    
    if 'go' in file_types:
        project_info["technologies"].add("Go")
    
    if 'rs' in file_types:
        project_info["technologies"].add("Rust")
    
    # 检查配置文件
    directories = " ".join(project_info["directories"])
    
    # 前端框架
    if 'package.json' in directories or 'package.json' in os.listdir():
        project_info["technologies"].add("Node.js")
        
        try:
            with open('package.json', 'r') as f:
                package_data = json.load(f)
                deps = {**package_data.get('dependencies', {}), **package_data.get('devDependencies', {})}
                
                if 'next' in deps:
                    project_info["technologies"].add("Next.js")
                
                if 'nuxt' in deps:
                    project_info["technologies"].add("Nuxt.js")
                
                if 'gatsby' in deps:
                    project_info["technologies"].add("Gatsby")
                
                if 'tailwindcss' in deps:
                    project_info["technologies"].add("Tailwind CSS")
                
                if '@angular/core' in deps:
                    project_info["technologies"].add("Angular")
        except:
            pass
    
    # 后端框架
    if 'requirements.txt' in directories or 'requirements.txt' in os.listdir():
        try:
            with open('requirements.txt', 'r') as f:
                content = f.read().lower()
                
                if 'django' in content:
                    project_info["technologies"].add("Django")
                
                if 'flask' in content:
                    project_info["technologies"].add("Flask")
                
                if 'fastapi' in content:
                    project_info["technologies"].add("FastAPI")
        except:
            pass
    
    # 移动开发
    if 'pubspec.yaml' in directories or 'pubspec.yaml' in os.listdir():
        project_info["technologies"].add("Flutter")
    
    if 'android' in directories or 'AndroidManifest.xml' in directories:
        project_info["technologies"].add("Android")
    
    if 'ios' in directories or 'Info.plist' in directories:
        project_info["technologies"].add("iOS")
    
    # 将集合转换为列表
    project_info["technologies"] = list(project_info["technologies"])

def call_ai_model(rule, project_info, model_url, api_key, model_name):
    """调用AI模型生成规则内容"""
    # 准备提示内容
    title = rule.get('title', '未命名规则')
    content = rule.get('content', '').strip()
    tags = rule.get('tags', [])
    
    # 准备项目信息
    file_types_info = ", ".join([f"{ext} ({count}个文件)" for ext, count in sorted(
        project_info["file_types"].items(), key=lambda x: x[1], reverse=True)[:10]])
    
    technologies = ", ".join(project_info["technologies"]) if project_info["technologies"] else "未检测到明确的技术栈"
    
    # 构建提示
    prompt = f"""您是一个专业的编程规则生成器。根据以下项目信息和规则模板，生成适合该项目的自定义规则。

项目信息:
- 文件类型分布: {file_types_info}
- 检测到的技术栈: {technologies}
- 目录结构: {project_info["directories"][:5] if len(project_info["directories"]) > 0 else "没有子目录"}

规则模板:
- 标题: {title}
- 标签: {', '.join(tags)}
- 内容:
{content[:500]}...

任务：
1. 分析项目的技术栈和文件类型
2. 根据规则模板和项目特点，生成定制化的编码规则
3. 确定适合该项目的文件匹配模式（globs）
4. 将规则内容格式化为Markdown列表，每条规则前面有一个减号(-)

请返回一个JSON对象，包含以下字段:
- globs: 文件匹配模式，例如 "**/*.{js,jsx}"
- content: 格式化的规则内容，每行一条规则，以减号开头

请确保返回的是有效的JSON格式。
"""

    # 如果有样本文件，添加到提示中
    sample_files = []
    for ext in ['js', 'ts', 'jsx', 'tsx', 'py', 'java', 'cs', 'php']:
        key = f"{ext}_files"
        if key in project_info and project_info[key]:
            # 只添加第一个样本文件
            sample = project_info[key][0]
            sample_files.append(f"样本文件 ({sample['path']}):\n```{ext}\n{sample['sample'][:300]}...\n```")
    
    if sample_files:
        # 最多添加2个样本文件
        prompt += "\n样本文件（帮助你理解项目代码风格）:\n" + "\n".join(sample_files[:2])
    
    try:
        # 构建请求
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "你是一个专业的编程规则生成器，擅长为各种编程语言和框架创建最佳实践规则。"},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.5,
            "max_tokens": 2000
        }
        
        # 发送请求
        logger.info(f"调用AI模型生成规则内容: {title}")
        response = requests.post(model_url, headers=headers, json=data)
        
        if response.status_code != 200:
            logger.error(f"AI模型调用失败: {response.status_code} - {response.text}")
            return None
        
        # 解析响应
        result = response.json()
        message_content = result.get('choices', [{}])[0].get('message', {}).get('content', '')
        
        # 尝试提取JSON
        try:
            # 查找JSON部分
            json_start = message_content.find('{')
            json_end = message_content.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_part = message_content[json_start:json_end]
                ai_result = json.loads(json_part)
                
                # 验证结果
                if 'globs' in ai_result and 'content' in ai_result:
                    logger.info(f"成功从AI模型获取定制规则内容")
                    return ai_result
            
            # 如果没有找到有效的JSON，尝试直接提取内容
            logger.warning("无法从AI响应中解析JSON，尝试直接提取内容")
            
            # 查找内容部分
            content_lines = []
            for line in message_content.split('\n'):
                if line.strip().startswith('-'):
                    content_lines.append(line)
            
            if content_lines:
                # 推断文件匹配模式
                globs = "**/*.{js,ts,jsx,tsx}"  # 默认值
                
                # 根据技术栈调整
                if "Python" in project_info["technologies"]:
                    globs = "**/*.py"
                elif "Java" in project_info["technologies"]:
                    globs = "**/*.java"
                elif "C#" in project_info["technologies"]:
                    globs = "**/*.cs"
                elif "React" in project_info["technologies"]:
                    globs = "**/*.{jsx,tsx}"
                
                return {
                    "globs": globs,
                    "content": "\n".join(content_lines)
                }
            
            logger.error("无法从AI响应中提取规则内容")
            return None
            
        except json.JSONDecodeError:
            logger.error(f"无法解析AI响应为JSON: {message_content[:200]}...")
            return None
        
    except Exception as e:
        logger.error(f"调用AI模型时出错: {str(e)}")
        return None

def convert_rule_to_mdc(rule, project_info, output_dir, use_ai=False, model_config=None):
    """将规则转换为MDC格式并保存，可选择使用AI模型定制内容"""
    try:
        # 提取规则属性
        title = rule.get('title', '未命名规则')
        content = rule.get('content', '').strip()
        tags = rule.get('tags', [])
        slug = rule.get('slug', '').lower() or title.lower().replace(' ', '-')
        
        # 创建文件名
        file_name = f"{slug}-practices"
        
        # 适用的文件类型和内容
        glob_pattern = "**/*.{js,ts,jsx,tsx}"  # 默认匹配所有JS/TS文件
        final_content = ""
        
        # 调用AI模型定制规则内容（如果启用）
        if use_ai and model_config and all(model_config.values()):
            model_url = model_config.get('model_url')
            api_key = model_config.get('api_key')
            model_name = model_config.get('model_name')
            
            ai_result = call_ai_model(rule, project_info, model_url, api_key, model_name)
            
            if ai_result:
                glob_pattern = ai_result.get('globs', glob_pattern)
                content = ai_result.get('content', content)
        
        # 如果没有使用AI或AI调用失败，使用基本处理
        if not final_content:
            # 根据标签和项目信息调整匹配模式
            if "React" in project_info.get("technologies", []) or "react" in tags:
                glob_pattern = "**/*.{jsx,tsx}"
            elif "Vue.js" in project_info.get("technologies", []) or "vue" in tags:
                glob_pattern = "**/*.vue"
            elif "Angular" in project_info.get("technologies", []) or "angular" in tags:
                glob_pattern = "**/*.{ts,html,scss}"
            elif "Python" in project_info.get("technologies", []) or "python" in tags:
                glob_pattern = "**/*.py"
            elif "C#" in project_info.get("technologies", []) or "csharp" in tags:
                glob_pattern = "**/*.cs"
            elif "Java" in project_info.get("technologies", []) or "java" in tags:
                glob_pattern = "**/*.java"
            
            # 处理内容，将其格式化为减号开头的列表项
            formatted_content = []
            for line in content.split('\n'):
                line = line.strip()
                if line and not line.startswith('-'):
                    if line.startswith('#') or line.startswith('*'):
                        # 保持标题或已有列表项格式
                        formatted_content.append(line)
                    else:
                        # 将普通文本转换为列表项
                        formatted_content.append(f"- {line}")
                elif line:
                    formatted_content.append(line)
            
            # 合并处理后的内容
            final_content = '\n'.join(formatted_content)
        else:
            final_content = content
        
        # 创建MDC内容
        mdc_content = MDC_TEMPLATE.format(
            name=file_name,
            description=title,
            globs=glob_pattern,
            content=final_content
        )
        
        # 保存到文件
        output_path = os.path.join(output_dir, f"{file_name}.mdc")
        
        # 确保目录存在
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # 使用二进制模式写入，确保正确编码
        with open(output_path, 'wb') as f:
            f.write(mdc_content.encode('utf-8'))
        
        logger.info(f"已创建规则文件: {output_path}")
        return output_path
    
    except Exception as e:
        logger.error(f"转换规则时出错: {str(e)}")
        return None

def check_model_config():
    """检查是否配置了AI模型"""
    # 使用配置管理模块获取配置
    config = get_model_config()
    
    # 验证配置是否完整
    if all([config.get('model_url'), config.get('api_key'), config.get('model_name')]):
        return {
            'model_url': config.get('model_url'),
            'api_key': config.get('api_key'),
            'model_name': config.get('model_name')
        }
    
    return None

def process_selected_rules(selected_rules, workspace_path, use_ai=False):
    """处理选中的规则，转换为MDC格式"""
    if not selected_rules:
        logger.warning("未选择任何规则，操作已取消")
        return
    
    # 创建规则输出目录
    output_dir = os.path.join(workspace_path, '.cursor', 'rules')
    os.makedirs(output_dir, exist_ok=True)
    
    # 分析项目结构
    project_info = analyze_project_structure(workspace_path)
    logger.info(f"项目技术栈: {', '.join(project_info['technologies'])}")
    
    # 检查AI模型配置
    model_config = None
    if use_ai:
        model_config = check_model_config()
        if not model_config:
            logger.warning("未提供完整的AI模型配置，将使用基本转换")
            use_ai = False
    
    # 转换并保存规则
    created_files = []
    total_rules = len(selected_rules)
    
    for i, rule in enumerate(selected_rules):
        logger.info(f"处理规则 {i+1}/{total_rules}: {rule.get('title', '未命名规则')}")
        file_path = convert_rule_to_mdc(rule, project_info, output_dir, use_ai, model_config)
        if file_path:
            created_files.append(file_path)
        
        # 添加一些延迟，避免API限制
        if use_ai and i < total_rules - 1:
            time.sleep(1)
    
    # 显示结果
    if created_files:
        logger.info(f"成功创建 {len(created_files)} 个规则文件:")
        for file_path in created_files:
            logger.info(f"- {file_path}")
    else:
        logger.error("未能创建任何规则文件")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='从本地JSON文件读取规则并提供选择界面')
    parser.add_argument('workspace_path', help='工作区路径，用于保存生成的规则文件')
    parser.add_argument('--rules-json', '-r', help='规则数据JSON文件路径', default='rules_data/rules.db.json')
    parser.add_argument('--no-ai', action='store_true', help='不使用AI模型定制规则内容')
    parser.add_argument('--selected-rule', help='预选的单个规则ID（slug）')
    parser.add_argument('--selected-rules', help='预选的多个规则ID（slug），用逗号分隔')
    args = parser.parse_args()
    
    # 确保工作区路径存在
    if not os.path.exists(args.workspace_path):
        logger.error(f"工作区路径不存在: {args.workspace_path}")
        return
    
    # 确保规则JSON文件存在
    rules_json_path = os.path.join(args.workspace_path, args.rules_json) if not os.path.isabs(args.rules_json) else args.rules_json
    if not os.path.exists(rules_json_path):
        logger.error(f"规则数据JSON文件不存在: {rules_json_path}")
        return
    
    # 加载规则数据
    rules = load_rules_from_json(rules_json_path)
    if not rules:
        logger.error("未能加载任何规则数据")
        return
    
    # 默认使用AI模型，除非明确指定--no-ai
    use_ai = not args.no_ai
    if use_ai:
        logger.info("将使用AI模型定制规则内容")
    else:
        logger.info("不使用AI模型定制规则内容")
    
    # 如果提供了预选规则，直接处理
    if args.selected_rule:
        # 处理单个预选规则
        selected_rule = None
        for rule in rules:
            if rule.get('slug') == args.selected_rule:
                selected_rule = rule
                break
        
        if selected_rule:
            logger.info(f"使用预选规则: {args.selected_rule}")
            process_selected_rules([selected_rule], args.workspace_path, use_ai)
        else:
            logger.error(f"找不到预选规则: {args.selected_rule}")
        return
    
    if args.selected_rules:
        # 处理多个预选规则
        rule_ids = args.selected_rules.split(',')
        selected_rules = []
        
        for rule_id in rule_ids:
            for rule in rules:
                if rule.get('slug') == rule_id.strip():
                    selected_rules.append(rule)
                    break
        
        if selected_rules:
            logger.info(f"使用预选规则: {args.selected_rules}")
            process_selected_rules(selected_rules, args.workspace_path, use_ai)
        else:
            logger.error(f"找不到任何预选规则: {args.selected_rules}")
        return
    
    # 显示规则列表供用户选择
    max_rules = display_rules_list(rules)
    
    # 用户选择规则
    selected_rules = select_rules(rules, max_rules)
    
    # 处理选中的规则
    process_selected_rules(selected_rules, args.workspace_path, use_ai)
    
    logger.info("规则选择和生成过程完成")

if __name__ == "__main__":
    main() 