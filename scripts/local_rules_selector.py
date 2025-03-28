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
from urllib.parse import urlparse
import re

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
    import io
    import locale
    
    # 获取系统默认编码
    system_encoding = locale.getpreferredencoding(False)
    
    # 尝试更可靠的编码设置方式
    try:
        # 检查是否在VSCode集成终端中运行
        if 'VSCODE_CWD' in os.environ or 'TERM_PROGRAM' in os.environ and os.environ['TERM_PROGRAM'] == 'vscode':
            # VSCode终端通常支持UTF-8
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
        else:
            # 使用系统默认编码
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding=system_encoding, errors='replace')
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding=system_encoding, errors='replace')
    except Exception as e:
        print(f"设置编码时出错: {e}")

# 设置日志格式
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8' if hasattr(logging, 'ENCODING') else None  # 兼容Python 3.8以下版本
)
logger = logging.getLogger(__name__)

# 全局设置
MODEL_TIMEOUT = 60  # API调用超时时间（秒）
MAX_RETRIES = 2     # 最大重试次数

def load_rules_from_json(json_path):
    """
    从JSON文件加载规则数据
    """
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            rules = json.load(f)
        
        # 预处理规则，确保格式一致
        processed_rules = []
        for rule in rules:
            # 确保规则具有必要的字段
            if isinstance(rule, dict):
                # 处理结构化规则格式
                if 'name' not in rule and 'title' in rule:
                    rule['name'] = rule['title']
                
                # 确保名称以.mdc结尾
                if 'name' in rule and not rule['name'].endswith('.mdc'):
                    rule['name'] = rule['name'] + '.mdc'
                
                # 如果没有description，但有title，使用title
                if 'description' not in rule and 'title' in rule:
                    rule['description'] = rule['title']
                
                # 如果没有globs，设置默认值
                if 'globs' not in rule:
                    rule['globs'] = '**/*.{js,ts,jsx,tsx}'
                
                # 确保有content字段
                if 'content' not in rule:
                    rule['content'] = '- 无规则内容'
                
                processed_rules.append(rule)
        
        logger.info(f"成功从{json_path}加载了{len(processed_rules)}条规则")
        return processed_rules
    except Exception as e:
        logger.error(f"加载规则数据失败: {str(e)}")
        return []

def display_rules_list(rules):
    """
    显示规则列表供用户选择
    """
    print("\n可用规则列表：")
    print("-" * 80)
    print(f"{'序号':<5}{'名称':<30}{'描述':<45}")
    print("-" * 80)
    
    max_rules = min(len(rules), 99)  # 最多显示99条规则
    
    for i in range(max_rules):
        rule = rules[i]
        # 截断过长的名称和描述
        name = rule.get('name', 'Unknown')[:28] + '..' if len(rule.get('name', 'Unknown')) > 28 else rule.get('name', 'Unknown')
        description = rule.get('description', '')[:43] + '..' if len(rule.get('description', '')) > 43 else rule.get('description', '')
        
        print(f"{i+1:<5}{name:<30}{description:<45}")
    
    print("-" * 80)
    return max_rules

def select_rules(rules, max_rules):
    """
    让用户选择要使用的规则
    """
    selected_indices = []
    
    while True:
        try:
            selection = input("\n请输入规则序号(1-{})，多个规则用逗号分隔，输入'all'选择所有规则: ".format(max_rules))
            
            if selection.lower() == 'all':
                logger.info("用户选择了所有规则")
                return rules[:max_rules]
            
            # 分割并验证输入
            indices = [int(idx.strip()) for idx in selection.split(',') if idx.strip()]
            
            # 验证输入是否有效
            if not indices:
                print("请至少选择一条规则")
                continue
            
            # 检查索引是否在有效范围内
            valid_indices = []
            for idx in indices:
                if 1 <= idx <= max_rules:
                    valid_indices.append(idx - 1)  # 转换为0-based索引
                else:
                    print(f"序号 {idx} 超出范围，有效范围是1-{max_rules}")
            
            if valid_indices:
                selected_indices = valid_indices
                break
            
        except ValueError:
            print("请输入有效的数字")
            continue
    
    # 根据索引选择规则
    selected_rules = [rules[idx] for idx in selected_indices]
    logger.info(f"用户选择了{len(selected_rules)}条规则")
    
    return selected_rules

def get_project_info(workspace_path):
    """
    分析项目结构，获取项目信息
    """
    project_info = {
        "file_types": [],
        "framework_hints": [],
        "total_files": 0,
        "directory_structure": []
    }
    
    # 检测文件类型和数量
    file_types = {}
    for root, dirs, files in os.walk(workspace_path):
        # 忽略隐藏目录和node_modules
        dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
        
        for file in files:
            ext = os.path.splitext(file)[1].lower()
            if ext:
                if ext in file_types:
                    file_types[ext] += 1
                else:
                    file_types[ext] = 1
                project_info["total_files"] += 1
    
    # 选择最常见的5种文件类型
    sorted_types = sorted(file_types.items(), key=lambda x: x[1], reverse=True)
    project_info["file_types"] = [{"extension": ext, "count": count} for ext, count in sorted_types[:5]]
    
    # 检测可能的框架
    framework_hints = []
    
    # 检测前端框架
    if os.path.exists(os.path.join(workspace_path, 'package.json')):
        try:
            with open(os.path.join(workspace_path, 'package.json'), 'r', encoding='utf-8') as f:
                pkg_data = json.load(f)
                deps = {**pkg_data.get('dependencies', {}), **pkg_data.get('devDependencies', {})}
                
                if 'react' in deps:
                    framework_hints.append("React")
                if 'vue' in deps:
                    framework_hints.append("Vue")
                if 'angular' in deps or '@angular/core' in deps:
                    framework_hints.append("Angular")
                if 'next' in deps:
                    framework_hints.append("Next.js")
                if 'nuxt' in deps:
                    framework_hints.append("Nuxt.js")
        except:
            pass
    
    # 检测后端框架
    if os.path.exists(os.path.join(workspace_path, 'requirements.txt')):
        try:
            with open(os.path.join(workspace_path, 'requirements.txt'), 'r', encoding='utf-8') as f:
                content = f.read()
                if 'django' in content.lower():
                    framework_hints.append("Django")
                if 'flask' in content.lower():
                    framework_hints.append("Flask")
                if 'fastapi' in content.lower():
                    framework_hints.append("FastAPI")
        except:
            pass
    
    project_info["framework_hints"] = framework_hints
    
    # 获取目录结构
    base_dirs = [d for d in os.listdir(workspace_path) 
                if os.path.isdir(os.path.join(workspace_path, d)) 
                and not d.startswith('.') 
                and d not in ['node_modules', 'venv', 'env', '__pycache__']]
    
    project_info["directory_structure"] = base_dirs
    
    return project_info

def convert_to_markdown(content):
    """
    将规则内容转换为格式良好的Markdown
    """
    if not content:
        return "- 无规则内容"
    
    # 如果已经是字符串，进行处理
    if isinstance(content, str):
        # 分割成行
        lines = content.split('\n')
        formatted_lines = []
        
        # 处理每一行
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 确保每行都以减号开头(Markdown列表项)
            if not line.startswith('-') and not line.startswith('#') and not line.startswith('*'):
                line = f"- {line}"
                
            # 处理可能的代码块
            if '```' in line:
                formatted_lines.append(line)
            else:
                # 对于普通文本，确保格式一致
                formatted_lines.append(line)
        
        # 如果处理后没有内容，添加默认行
        if not formatted_lines:
            formatted_lines.append("- 无规则内容")
            
        # 合并成Markdown文本
        markdown_content = '\n'.join(formatted_lines)
        
        # 检查是否有代码段，如果有确保格式正确
        if '```' in markdown_content:
            # 确保代码块前后有空行
            markdown_content = markdown_content.replace('\n```', '\n\n```')
            markdown_content = markdown_content.replace('```\n', '```\n\n')
        
        return markdown_content
    
    # 如果是其他类型（列表、字典等），尝试转换
    elif isinstance(content, list):
        # 如果是列表，将每个项目转换为列表项
        return '\n'.join([f"- {item}" for item in content if item])
    elif isinstance(content, dict):
        # 如果是字典，将键值对转换为列表项
        return '\n'.join([f"- {k}: {v}" for k, v in content.items()])
    else:
        # 其他类型，转为字符串后添加减号
        return f"- {str(content)}"

def analyze_with_ai(content, project_info, config):
    """
    使用AI模型分析内容并生成规则，使用流式处理实时生成规则文件
    
    @param content - 需要分析的内容
    @param project_info - 项目信息
    @param config - AI模型配置
    @yield Tuple[str, str, str, str] - 生成规则元组 (name, description, globs, content)
    """
    try:
        # 准备系统提示词
        system_prompt = """你是一个专业的代码分析助手，专门负责创建和组织 Cursor MDC 规则文件。
你需要将输入的内容转换为多个规则，每个规则都应该遵循以下规范：

1. 命名规范（name）：
   - 使用 kebab-case（小写字母和连字符）
   - 格式：{技术}-best-practices 或 {技术}-{功能}-practices
   - 示例：nextjs-best-practices, typescript-validation-practices
   - 常见前缀：nextjs, react, typescript, tailwindcss, shadcn-ui, radix-ui, zustand, tanstack-query, zod

2. 文件匹配（glob_pattern）：
   - 针对特定技术和文件类型
   - 常见模式：**/*.{ts,tsx} 或 **/*.{ts,tsx,js,jsx}
   - 可以指定具体目录：app/**/*.{ts,tsx}, components/**/*.{ts,tsx}
   - 避免过于宽泛的匹配

3. 描述规范（description）：
   - 简洁明了的一句话描述
   - 格式：Best practices for [技术/领域] [具体方面]
   - 示例：Best practices for Next.js applications and routing
   - 突出核心技术和主要目的

4. 内容规范（content）：
   - 使用无序列表（减号 + 空格开头）
   - 每条规则独立且可执行
   - 包含具体的技术实践
   - 使用简洁的技术术语
   - 避免过于理论化的描述
   - 保持 4-6 条核心规则
   - 每条规则一行，以换行符分隔
   - 规则结尾不加标点符号

请直接返回 JSON 数组，不要添加任何 Markdown 格式。"""

        # 准备项目信息字符串
        project_info_str = f"""项目信息:
- 主要文件类型: {', '.join([f"{item['extension']}({item['count']}个)" for item in project_info['file_types']])}
- 检测到的框架/库: {', '.join(project_info['framework_hints']) if project_info['framework_hints'] else '未检测到明确框架'}
- 目录结构: {', '.join(project_info['directory_structure'])}
- 文件总数: {project_info['total_files']}
"""

        # 准备用户提示内容
        user_prompt = f"""分析以下内容并创建多个 Cursor 规则文件 (.mdc)，参考以下示例格式：

{{
  "name": "nextjs-best-practices",
  "glob_pattern": "**/*.{{ts,tsx}}",
  "description": "Best practices for Next.js applications and routing",
  "content": "- Favor React Server Components (RSC) for improved performance and SEO\\n- Use the App Router for better routing and data fetching\\n- Implement dynamic imports for code splitting and lazy loading\\n- Optimize images using Next.js Image component with WebP format and size data"
}}

{{
  "name": "typescript-best-practices",
  "glob_pattern": "**/*.{{ts,tsx}}",
  "description": "Best practices for TypeScript development and type safety",
  "content": "- Enable strict mode in tsconfig for better type checking\\n- Use type inference where possible but add explicit types for clarity\\n- Implement custom type guards for runtime type checking\\n- Use generics for reusable components and utility functions"
}}

{project_info_str}

请分析以下内容并生成多个规则：

{content}

返回一个有效的 JSON 数组，每个规则对象必须包含上述四个字段，content内容必须以中文返回，并严格遵循示例格式。"""

        # 调用 API
        model_url = config.get('model_url')
        api_key = config.get('api_key')
        model_name = config.get('model_name')
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.2,
            "max_tokens": 2048,
            "top_p": 0.95,
            "n": 1,
            "stream": True,
            "stop": None
        }
        
        logger.info("正在调用 AI API（流式处理模式）...")
        response = requests.post(model_url, headers=headers, json=data, stream=True)
        
        if response.status_code != 200:
            logger.error(f"API 调用失败: {response.status_code}")
            logger.error(f"错误信息: {response.text}")
            return
            
        # 用于存储JSON文本
        json_text = ""
        in_json = False
        
        # 处理流式响应
        for line in response.iter_lines():
            if line:
                try:
                    if line.startswith(b"data: "):
                        json_str = line[6:].decode('utf-8')
                        if json_str.strip() == "[DONE]":
                            break
                            
                        chunk = json.loads(json_str)
                        if "choices" in chunk and chunk["choices"]:
                            content_delta = chunk["choices"][0].get("delta", {}).get("content", "")
                            if content_delta:
                                # 检测JSON数组的开始和结束
                                if '[' in content_delta:
                                    in_json = True
                                
                                if in_json:
                                    json_text += content_delta
                                    
                                    # 尝试解析完整的JSON对象
                                    if '},' in json_text or '}]' in json_text:
                                        try:
                                            # 提取可能完整的JSON对象
                                            while True:
                                                obj_start = json_text.find('{')
                                                obj_end = json_text.find('},')
                                                if obj_end == -1:
                                                    obj_end = json_text.find('}]')
                                                
                                                if obj_start != -1 and obj_end != -1:
                                                    obj_text = json_text[obj_start:obj_end+1]
                                                    try:
                                                        rule = json.loads(obj_text)
                                                        # 生成规则元组
                                                        yield (
                                                            rule.get("name", "unknown"),
                                                            rule.get("description", ""),
                                                            rule.get("glob_pattern", "**/*"),
                                                            rule.get("content", "")
                                                        )
                                                        # 移除已处理的对象
                                                        json_text = json_text[obj_end+1:]
                                                    except json.JSONDecodeError:
                                                        break
                                                else:
                                                    break
                                        except Exception as e:
                                            logger.warning(f"解析规则时出错: {str(e)}")
                                            
                except Exception as e:
                    logger.warning(f"处理数据块时出错: {str(e)}")
                    continue
        
    except Exception as e:
        logger.error(f"AI 分析出错: {str(e)}")
        yield ("error-rule.mdc", f"Error: {str(e)}", "**/*", "- 处理出错，请检查日志")

def process_selected_rules(selected_rules, workspace_path, use_ai=True):
    """
    处理选中的规则，使用AI定制内容并保存为MDC文件
    采用流式处理方式，每处理完一个规则就立即保存
    """
    if not selected_rules:
        logger.warning("没有选择任何规则")
        return
    
    # 准备输出目录
    output_dir = os.path.join(workspace_path, '.cursor', 'rules')
    os.makedirs(output_dir, exist_ok=True)
    
    # 获取AI模型配置
    config = get_model_config() if use_ai else None
    
    # 项目分析
    logger.info("分析项目结构中...")
    project_info = get_project_info(workspace_path)
    logger.info(f"项目分析完成: 检测到{len(project_info['file_types'])}种主要文件类型, {len(project_info['framework_hints'])}种框架/库")
    
    # 计算总规则数量
    total_rules = len(selected_rules)
    successful = 0
    rules_generated = 0
    
    # 逐个处理每条规则
    for i, rule in enumerate(selected_rules):
        try:
            # 确保规则是标准格式
            rule_data = prep_rule_data(rule)
            
            rule_name = rule_data.get('name', 'Unknown')
            logger.info(f"处理规则: {rule_name}")
            
            # 使用AI定制规则内容
            if use_ai and config:
                logger.info(f"正在调用 AI API (流式处理模式)...")
                
                # 获取规则内容
                rule_content = rule_data.get('content', '- 没有提供规则内容')
                
                # 将规则内容转换为Markdown格式
                markdown_content = convert_to_markdown(rule_content)
                
                # 调用AI分析规则内容并生成多个规则
                for rule_tuple in analyze_with_ai(markdown_content, project_info, config):
                    # 处理并保存规则
                    name, description, glob_pattern, content = rule_tuple
                    
                    # 确保name以.mdc结尾
                    if not name.endswith('.mdc'):
                        name = f"{name}.mdc"
                    
                    # 创建MDC内容
                    mdc_content = f"""---
name: {name}
description: {description}
globs: {glob_pattern}
---

{content}
"""
                    
                    # 保存MDC文件
                    output_path = os.path.join(output_dir, name)
                    with open(output_path, 'wb') as f:
                        f.write(mdc_content.encode('utf-8'))
                    
                    rules_generated += 1
                    successful += 1
                    logger.info(f"已创建规则文件: {output_path}")
                
                if rules_generated > 0:
                    logger.info(f"已处理 {rules_generated} 个规则...")
                else:
                    # 如果没有生成规则，直接保存原始规则
                    logger.info("未能生成规则，使用原始规则...")
                    
                    # 保存原始规则
                    name = rule_data.get('name', 'unknown_rule.mdc')
                    description = rule_data.get('description', 'Auto-generated rule')
                    glob_pattern = rule_data.get('globs', '**/*')
                    content = rule_data.get('content', '- No rule content')
                    
                    # 确保name以.mdc结尾
                    if not name.endswith('.mdc'):
                        name = f"{name}.mdc"
                    
                    # 创建MDC内容
                    mdc_content = f"""---
name: {name}
description: {description}
globs: {glob_pattern}
---

{content}
"""
                    
                    # 保存MDC文件
                    output_path = os.path.join(output_dir, name)
                    with open(output_path, 'wb') as f:
                        f.write(mdc_content.encode('utf-8'))
                    
                    successful += 1
                    logger.info(f"已创建规则文件: {output_path}")
            else:
                # 不使用AI，直接保存规则
                name = rule_data.get('name', 'unknown_rule.mdc')
                description = rule_data.get('description', 'Auto-generated rule')
                glob_pattern = rule_data.get('globs', '**/*')
                content = rule_data.get('content', '- No rule content')
                
                # 确保name以.mdc结尾
                if not name.endswith('.mdc'):
                    name = f"{name}.mdc"
                
                # 创建MDC内容
                mdc_content = f"""---
name: {name}
description: {description}
globs: {glob_pattern}
---

{content}
"""
                
                # 保存MDC文件
                output_path = os.path.join(output_dir, name)
                with open(output_path, 'wb') as f:
                    f.write(mdc_content.encode('utf-8'))
                
                successful += 1
                logger.info(f"已创建规则文件: {output_path}")
                
        except Exception as e:
            logger.error(f"处理规则时出错: {str(e)}")
    
    # 总结处理结果
    logger.info(f"成功处理完成! 共创建了 {successful} 个规则文件。")
    logger.info("处理完成!")

def prep_rule_data(rule):
    """
    预处理规则数据，确保格式统一
    """
    if not isinstance(rule, dict):
        logger.warning(f"规则不是字典格式: {rule}")
        # 尝试转换为字典
        try:
            if isinstance(rule, str):
                rule = json.loads(rule)
            else:
                rule = {"content": str(rule)}
        except:
            rule = {"content": str(rule)}
    
    # 创建标准规则结构的副本
    rule_data = {}
    
    # 处理name字段
    if 'name' in rule:
        rule_data['name'] = rule['name']
    elif 'title' in rule:
        rule_data['name'] = rule['title']
    else:
        rule_data['name'] = 'unknown_rule.mdc'
    
    # 确保name以.mdc结尾
    if not rule_data['name'].endswith('.mdc'):
        rule_data['name'] = rule_data['name'] + '.mdc'
    
    # 处理description字段
    if 'description' in rule:
        rule_data['description'] = rule['description']
    elif 'title' in rule:
        rule_data['description'] = rule['title']
    else:
        rule_data['description'] = '自动生成的规则'
    
    # 处理globs字段
    if 'globs' in rule:
        rule_data['globs'] = rule['globs']
    elif 'glob_pattern' in rule:
        rule_data['globs'] = rule['glob_pattern']
    else:
        rule_data['globs'] = '**/*.{js,ts,jsx,tsx}'
    
    # 处理content字段
    if 'content' in rule:
        rule_data['content'] = rule['content']
    else:
        rule_data['content'] = '- 规则内容未定义'
    
    # 复制其他可能有用的字段
    for key in rule:
        if key not in rule_data and key not in ['name', 'title', 'description', 'globs', 'glob_pattern', 'content']:
            rule_data[key] = rule[key]
    
    return rule_data

def main():
    """
    主函数
    """
    parser = argparse.ArgumentParser(description='本地规则选择器和生成工具')
    # 添加工作区位置参数（可选）
    parser.add_argument('workspace', nargs='?', default='.', help='项目工作区路径')
    parser.add_argument('--rules-json', default='rules_data/rules.json', help='规则数据JSON文件路径')
    parser.add_argument('--workspace', dest='workspace_named', help='项目工作区路径（与位置参数二选一）')
    parser.add_argument('--selected-rule', help='直接选择指定规则(通过slug)')
    parser.add_argument('--output-dir', help='自定义输出目录')
    parser.add_argument('--debug', action='store_true', help='启用调试模式，显示更多日志信息')
    args = parser.parse_args()
    
    # 如果同时提供了位置参数和命名参数形式的workspace，优先使用命名参数
    workspace_path = os.path.abspath(args.workspace_named if args.workspace_named else args.workspace)
    
    # 设置调试模式
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    # 设置工作区路径
    if not os.path.isdir(workspace_path):
        logger.error(f"工作区路径不存在或不是目录: {workspace_path}")
        print(f"错误: 工作区路径不存在或不是目录 - {workspace_path}")
        return
    
    # 设置输出目录
    if args.output_dir:
        output_dir = os.path.abspath(args.output_dir)
        logger.info(f"使用指定的输出目录: {output_dir}")
        # 确保目录存在
        os.makedirs(output_dir, exist_ok=True)
    else:
        # 默认输出目录
        output_dir = os.path.join(workspace_path, '.cursor', 'rules')
    
    # 确保规则JSON文件存在
    rules_json_path = os.path.join(workspace_path, args.rules_json) if not os.path.isabs(args.rules_json) else args.rules_json
    
    # 尝试多种可能的规则文件名，增强兼容性
    if not os.path.exists(rules_json_path):
        logger.debug(f"指定的规则数据文件不存在，尝试替代文件: {rules_json_path}")
        
        # 尝试替代文件名
        alt_paths = [
            os.path.join(os.path.dirname(rules_json_path), "rules.db.json"),
            os.path.join(workspace_path, "rules_data", "rules.db.json"),
            os.path.join(workspace_path, "rules.db.json")
        ]
        
        for alt_path in alt_paths:
            logger.debug(f"尝试替代路径: {alt_path}")
            if os.path.exists(alt_path):
                logger.info(f"使用替代规则数据文件: {alt_path}")
                print(f"注意: 使用替代规则数据文件 - {alt_path}")
                rules_json_path = alt_path
                break
    
    if not os.path.exists(rules_json_path):
        logger.error(f"规则数据JSON文件不存在: {rules_json_path}")
        print(f"错误: 规则数据文件不存在 - {rules_json_path}")
        print("请确保规则数据文件存在于以下位置之一:")
        print(f"  - {args.rules_json}")
        print(f"  - {os.path.join(workspace_path, 'rules_data', 'rules.json')}")
        print(f"  - {os.path.join(workspace_path, 'rules_data', 'rules.db.json')}")
        return
    
    # 加载规则数据
    rules = load_rules_from_json(rules_json_path)
    if not rules:
        logger.error("未能加载任何规则数据")
        print("错误: 未能加载任何规则数据")
        return
    
    # 如果提供了选择规则
    if args.selected_rule:
        # 处理单个选择规则
        selected_rule = next((rule for rule in rules if rule.get('slug') == args.selected_rule), None)
        
        if selected_rule:
            logger.info(f"使用指定规则: {args.selected_rule}")
            print(f"使用指定规则: {selected_rule.get('name', args.selected_rule)}")
            process_selected_rules([selected_rule], workspace_path, True)
        else:
            logger.error(f"找不到指定规则: {args.selected_rule}")
            print(f"错误: 找不到指定规则 - {args.selected_rule}")
        return

    # 显示规则列表供用户选择
    print("\n请从以下规则列表中选择需要的规则:")
    max_rules = display_rules_list(rules)

    # 用户选择规则
    selected_rules = select_rules(rules, max_rules)

    # 处理选中的规则
    process_selected_rules(selected_rules, workspace_path, True)

    logger.info("规则选择和生成过程完成")
    print("\n任务完成！感谢使用Cursor规则生成器。")

if __name__ == "__main__":
    main() 