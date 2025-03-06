#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 从Cursor Directory获取规则并转换为Cursor project rules
"""

import os
import sys
import json
import re
import shutil
import logging
import argparse
import requests
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from urllib.parse import urljoin
from bs4 import BeautifulSoup

# 设置控制台编码，避免乱码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer)
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    encoding='utf-8'  # 确保日志使用UTF-8编码
)
logger = logging.getLogger(__name__)

# 常量
CURSOR_DIRECTORY_URL = "https://cursor.directory/rules/"
MDC_TEMPLATE = """---
name: {name}.mdc
description: {description}
globs: {globs}
---

{content}
"""

def fetch_from_directory():
    """从Cursor Directory获取规则，带有更好的错误处理"""
    try:
        logger.info(f"正在尝试连接 {CURSOR_DIRECTORY_URL}...")
        
        # 添加超时和禁用SSL验证（仅用于调试）
        response = requests.get(
            CURSOR_DIRECTORY_URL, 
            timeout=10,
            verify=True,  # 生产环境应设为True，调试时可设为False
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        response.raise_for_status()
        logger.info("成功连接到网站")
        return response.text
    except requests.exceptions.SSLError as e:
        logger.error(f"SSL证书验证失败: {str(e)}")
        logger.error("可能需要禁用SSL验证（仅限调试）或更新证书")
        return None
    except requests.exceptions.ConnectionError as e:
        logger.error(f"连接错误: {str(e)}")
        logger.error("可能是网络问题或网站不可用")
        return None
    except requests.exceptions.Timeout:
        logger.error(f"连接超时: 请求花费了太长时间")
        return None
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP错误: {str(e)}")
        return None
    except Exception as e:
        logger.error(f"未知错误: {str(e)}")
        return None


class RuleFetcher:
    """从Cursor Directory获取规则"""
    
    def __init__(self, base_url: str = CURSOR_DIRECTORY_URL):
        """
        初始化抓取器
        
        @param base_url - Cursor Directory基础URL
        """
        self.base_url = base_url
        
    def fetch_rules(self) -> List[Dict[str, Any]]:
        """
        获取所有规则
        
        @returns 规则列表
        """
        logger.info(f"从 {self.base_url} 获取规则...")
        rules = []
        
        try:
            # 使用更强大的fetch函数
            content = fetch_from_directory()
            if not content:
                logger.error("无法获取网站内容")
                return rules
                
            soup = BeautifulSoup(content, 'html.parser')
            rule_cards = soup.select('.rule-card')
            
            if not rule_cards:
                logger.warning("未找到规则卡片，可能网站结构已更改")
                return rules
                
            for card in rule_cards:
                rule = self._parse_rule_card(card)
                if rule:
                    rules.append(rule)
            
            logger.info(f"成功获取到 {len(rules)} 条规则")
            return rules
            
        except Exception as e:
            logger.error(f"解析规则时出错: {str(e)}")
            return rules
    
    def _parse_rule_card(self, card) -> Optional[Dict[str, Any]]:
        """
        解析规则卡片
        
        @param card - BeautifulSoup卡片元素
        @returns 规则字典或None
        """
        try:
            # 提取ID
            card_id = card.get('id', '')
            if not card_id:
                card_id = f"rule-{hash(card.text)}"
                
            # 提取标题
            title_elem = card.select_one('.rule-title')
            title = title_elem.text.strip() if title_elem else "未知规则"
            
            # 提取描述
            desc_elem = card.select_one('.rule-description')
            description = desc_elem.text.strip() if desc_elem else ""
            
            # 提取作者
            author_elem = card.select_one('.rule-author')
            author = author_elem.text.strip() if author_elem else "未知作者"
            
            # 提取内容
            content_elem = card.select_one('.rule-content')
            content = content_elem.text.strip() if content_elem else ""
            
            # 提取文件匹配模式
            glob_elem = card.select_one('.rule-glob')
            glob_pattern = glob_elem.text.strip() if glob_elem else "**/*.{ts,tsx,js,jsx}"
            
            # 为规则创建名称（kebab-case格式）
            name = self._generate_rule_name(title)
            
            return {
                "id": card_id,
                "name": name,
                "title": title,
                "description": description,
                "author": author,
                "content": content,
                "glob_pattern": glob_pattern
            }
            
        except Exception as e:
            logger.error(f"解析规则卡片时出错: {str(e)}")
            return None
    
    def _generate_rule_name(self, title: str) -> str:
        """
        从标题生成规则名称
        
        @param title - 规则标题
        @returns kebab-case格式的名称
        """
        # 删除非字母数字字符，将空格替换为连字符
        name = re.sub(r'[^a-zA-Z0-9\s]', '', title.lower())
        name = re.sub(r'\s+', '-', name)
        
        # 确保名称以常见前缀开头
        prefixes = ["nextjs", "react", "typescript", "tailwindcss", "zustand"]
        if not any(name.startswith(prefix) for prefix in prefixes):
            # 从标题中提取可能的前缀
            words = title.lower().split()
            if words and words[0] not in ["best", "good", "recommended"]:
                prefix = words[0]
            else:
                prefix = "general"
            
            # 添加后缀
            name = f"{prefix}-{name}" if not name.startswith(prefix) else name
        
        # 添加practices后缀（如果没有）
        if not name.endswith("practices"):
            name = f"{name}-practices"
            
        return name


class RuleConverter:
    """将规则转换为Cursor project rules格式"""
    
    def __init__(self, workspace_path: str):
        """
        初始化转换器
        
        @param workspace_path - 工作区路径
        """
        self.workspace_path = Path(workspace_path)
        self.rules_dir = self.workspace_path / '.cursor' / 'rules'
        
    def convert_rules(self, rules: List[Dict[str, Any]]) -> bool:
        """
        转换规则
        
        @param rules - 规则列表
        @returns 是否成功
        """
        logger.info(f"开始转换 {len(rules)} 条规则...")
        
        try:
            # 创建目录
            self.rules_dir.mkdir(parents=True, exist_ok=True)
            
            # 清理现有规则文件
            for file in self.rules_dir.glob('*.mdc'):
                file.unlink()
                
            # 转换规则
            for rule in rules:
                self._convert_rule(rule)
                
            logger.info("规则转换完成")
            return True
            
        except Exception as e:
            logger.error(f"转换规则时出错: {str(e)}")
            return False
    
    def _convert_rule(self, rule: Dict[str, Any]) -> None:
        """
        转换单个规则
        
        @param rule - 规则字典
        """
        name = rule.get('name', 'unknown-rule')
        description = rule.get('description', '')
        glob_pattern = rule.get('glob_pattern', '**/*.{ts,tsx,js,jsx}')
        content = rule.get('content', '')
        
        # 格式化内容（确保每行以减号开头）
        formatted_content = self._format_content(content)
        
        # 创建MDC文件内容
        mdc_content = MDC_TEMPLATE.format(
            name=name,
            description=description,
            globs=glob_pattern,
            content=formatted_content
        )
        
        # 写入文件（使用二进制模式）
        file_path = self.rules_dir / f"{name}.mdc"
        with open(file_path, 'wb') as f:
            f.write(mdc_content.encode('utf-8'))
            
        logger.info(f"已创建规则文件: {file_path.name}")
    
    def _format_content(self, content: str) -> str:
        """
        格式化规则内容
        
        @param content - 原始内容
        @returns 格式化后的内容
        """
        lines = content.strip().split('\n')
        formatted_lines = []
        
        for line in lines:
            line = line.strip()
            if line:
                # 如果行不以减号开头，添加减号
                if not line.startswith('-'):
                    line = f"- {line}"
                    
                # 确保行末没有标点符号
                if line[-1] in ['.', ';', ',']:
                    line = line[:-1]
                    
                formatted_lines.append(line)
                
        return '\n'.join(formatted_lines)


class AIModelClient:
    """AI模型客户端类，用于调用AI模型API生成规则"""
    
    def __init__(self, model_url: str, api_key: str, model_name: str):
        """
        初始化AI模型客户端
        
        @param model_url - 模型API的URL
        @param api_key - API密钥
        @param model_name - 模型名称
        """
        self.model_url = model_url
        self.api_key = api_key
        self.model_name = model_name
        
    def generate_rules(self, content: str) -> List[Dict[str, Any]]:
        """
        使用AI模型生成规则
        
        @param content - 需要分析的内容
        @returns 生成的规则列表
        """
        if not self.model_url or not self.api_key:
            logger.error("模型URL或API密钥未配置")
            return []
            
        logger.info(f"使用模型 {self.model_name} 生成规则...")
        
        try:
            # 构建系统提示
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

            # 构建用户提示
            user_prompt = f"""分析以下内容并创建 Cursor 规则文件 (.mdc)，参考以下示例格式：

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
  "content": "- Use type inference where possible but add explicit types for clarity\\n- Implement custom type guards for runtime type checking\\n- Use generics for reusable components and utility functions"
}}

请分析以下内容并生成规则：

{content}

返回一个有效的 JSON 数组，每个规则对象必须包含上述四个字段，并严格遵循示例格式。"""

            # 调用API
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": 2048
            }
            
            logger.info("正在调用AI模型API...")
            response = requests.post(self.model_url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            if "choices" in result and result["choices"]:
                content = result["choices"][0].get("message", {}).get("content", "")
                
                try:
                    # 提取JSON内容
                    json_start = content.find('[')
                    json_end = content.rfind(']') + 1
                    
                    if json_start != -1 and json_end != -1:
                        json_content = content[json_start:json_end]
                        rules = json.loads(json_content)
                        
                        logger.info(f"成功生成 {len(rules)} 条规则")
                        return rules
                    else:
                        logger.error("无法从响应中提取JSON数组")
                        return []
                        
                except json.JSONDecodeError as e:
                    logger.error(f"解析JSON时出错: {str(e)}")
                    return []
            else:
                logger.error("API响应中没有发现有效内容")
                return []
                
        except requests.RequestException as e:
            logger.error(f"API请求失败: {str(e)}")
            return []
            
        except Exception as e:
            logger.error(f"生成规则时出错: {str(e)}")
            return []


def get_sample_rules() -> List[Dict[str, Any]]:
    """
    获取样例规则，当网络获取失败时使用
    
    @returns 样例规则列表
    """
    return [
        {
            "id": "sample-rule-1",
            "name": "react-best-practices",
            "title": "React Best Practices",
            "description": "React开发最佳实践规则",
            "author": "Cursor团队",
            "content": "- 使用函数组件和Hooks而不是类组件\n- 避免在渲染函数中创建新函数\n- 使用React.memo()优化性能\n- 对复杂组件进行适当拆分\n- 使用ESLint和Prettier保持代码风格一致",
            "glob_pattern": "**/*.{tsx,jsx}"
        },
        {
            "id": "sample-rule-2",
            "name": "typescript-best-practices",
            "title": "TypeScript Best Practices",
            "description": "TypeScript类型安全最佳实践",
            "author": "Cursor团队",
            "content": "- 尽量使用类型推断，但在必要时添加显式类型\n- 避免使用any类型\n- 使用接口定义组件props\n- 对异步操作返回值进行类型定义\n- 使用泛型创建可复用组件",
            "glob_pattern": "**/*.{ts,tsx}"
        },
        {
            "id": "sample-rule-3",
            "name": "nextjs-best-practices",
            "title": "Next.js Best Practices",
            "description": "Next.js应用开发最佳实践",
            "author": "Cursor团队",
            "content": "- 使用服务器组件(RSC)提高性能\n- 实现增量静态生成(ISR)\n- 使用Image组件优化图片加载\n- 利用动态导入进行代码分割\n- 配置适当的缓存策略",
            "glob_pattern": "**/*.{ts,tsx,js,jsx}"
        }
    ]


def create_template_file(selected_rule_ids: Optional[List[str]] = None, model_config: Optional[Dict[str, str]] = None) -> Tuple[List[Dict[str, Any]], bool]:
    """
    创建模板文件并获取规则
    
    @param selected_rule_ids - 选定的规则ID列表
    @param model_config - 模型配置信息
    @returns (规则列表，是否成功)
    """
    # 首先尝试从网站获取规则
    fetcher = RuleFetcher()
    online_rules = fetcher.fetch_rules()
    
    # 获取所有规则（在线或样例）
    all_rules = online_rules if online_rules else get_sample_rules()
    
    if not online_rules:
        logger.warning("从在线源获取规则失败，使用本地样例规则代替")
    
    # 如果没有从网站获取到规则且有模型配置，尝试使用AI生成规则
    if not all_rules and model_config and model_config.get('url') and model_config.get('api_key'):
        logger.info("尝试使用AI模型生成规则")
        ai_client = AIModelClient(
            model_url=model_config.get('url', ''),
            api_key=model_config.get('api_key', ''),
            model_name=model_config.get('model_name', 'deepseek-ai/DeepSeek-R1-Distill-Llama-8B')
        )
        
        # 这里可以提供一些示例内容让AI生成规则
        example_content = """
        常见的Cursor规则包括：
        
        1. React最佳实践：
           - 使用函数组件和Hooks而不是类组件
           - 使用React.memo()优化性能
           - 适当拆分组件保持单一职责
           - 使用Context API管理全局状态
        
        2. TypeScript最佳实践：
           - 启用严格模式检查
           - 使用接口定义props类型
           - 使用泛型创建可复用组件
           - 避免使用any类型
        
        3. Next.js最佳实践：
           - 使用服务器组件提高性能
           - 实现增量静态生成(ISR)
           - 使用Image组件优化图片
           - 配置适当的缓存策略
        """
        
        ai_rules = ai_client.generate_rules(example_content)
        if ai_rules:
            all_rules = ai_rules
        else:
            logger.warning("AI生成规则失败，使用本地样例规则")
            all_rules = get_sample_rules()
    
    if not all_rules:
        logger.error("无法获取规则")
        return [], False
        
    # 如果提供了规则ID，筛选规则
    if selected_rule_ids:
        rules = [r for r in all_rules if r.get('id') in selected_rule_ids]
        if not rules:
            logger.warning("未找到指定的规则ID，使用所有规则")
            rules = all_rules
    else:
        rules = all_rules
        
    return rules, True


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='从Cursor Directory获取规则并转换为Cursor project rules')
    parser.add_argument('workspace_path', help='工作区路径')
    parser.add_argument('--rule-ids', nargs='*', help='要获取的规则ID列表')
    parser.add_argument('--model-url', help='AI模型API的URL')
    parser.add_argument('--api-key', help='AI模型的API密钥')
    parser.add_argument('--model-name', default='deepseek-ai/DeepSeek-R1-Distill-Llama-8B', help='使用的AI模型名称')
    parser.add_argument('--use-samples', action='store_true', help='直接使用样例规则，跳过网络请求')
    
    args = parser.parse_args()
    
    # 检查环境变量，判断是否使用样例规则
    use_samples = args.use_samples or os.environ.get('USE_SAMPLE_RULES', '0').lower() in ('1', 'true', 'yes')
    
    try:
        if use_samples:
            logger.info("使用样例规则模式，跳过网络请求")
            rules = get_sample_rules()
            success = bool(rules)
        else:
            # 构建模型配置
            model_config = None
            if args.model_url and args.api_key:
                model_config = {
                    'url': args.model_url,
                    'api_key': args.api_key,
                    'model_name': args.model_name
                }
                logger.info(f"使用模型配置: URL={args.model_url}, 模型={args.model_name}")
            else:
                logger.warning("未提供AI模型配置，将仅尝试从网站获取规则")
                
            # 获取规则
            rules, success = create_template_file(args.rule_ids, model_config)
            
        if not success:
            logger.error("获取规则失败")
            sys.exit(1)
            
        # 转换规则
        converter = RuleConverter(args.workspace_path)
        if not converter.convert_rules(rules):
            logger.error("转换规则失败")
            sys.exit(1)
            
        logger.info(f"已成功创建 {len(rules)} 个规则文件")
            
    except Exception as e:
        logger.error(f"程序执行出错: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main() 