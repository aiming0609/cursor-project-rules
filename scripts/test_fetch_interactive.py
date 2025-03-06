#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 交互式测试从Cursor Directory获取规则的脚本
"""

import os
import sys
import json
import logging
import requests
import argparse
from bs4 import BeautifulSoup
from pathlib import Path

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

# 常量
CURSOR_DIRECTORY_URL = "https://cursor.directory/rules/"

def get_page_content(url=None, offline_file=None):
    """获取页面内容，支持在线和离线模式"""
    if offline_file and os.path.exists(offline_file):
        logger.info(f"使用离线HTML文件: {offline_file}")
        try:
            with open(offline_file, 'r', encoding='utf-8') as f:
                content = f.read()
            logger.info(f"成功读取离线文件，长度: {len(content)} 字节")
            return content
        except Exception as e:
            logger.error(f"读取离线文件时出错: {str(e)}")
            return None
    
    if not url:
        url = CURSOR_DIRECTORY_URL
    
    logger.info(f"正在获取页面内容: {url}")
    try:
        response = requests.get(
            url, 
            timeout=15,
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        if response.status_code != 200:
            logger.error(f"获取页面失败，HTTP状态码: {response.status_code}")
            return None
            
        content = response.text
        logger.info(f"成功获取页面内容，长度: {len(content)} 字节")
        
        # 保存HTML以便未来离线分析
        with open("cursor_directory_latest.html", "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"页面内容已保存到: cursor_directory_latest.html")
            
        return content
    except Exception as e:
        logger.error(f"获取页面内容时出错: {str(e)}")
        return None

def explore_html_structure(html_content):
    """探索HTML结构并显示有用的信息"""
    if not html_content:
        logger.error("没有HTML内容可分析")
        return None
        
    logger.info("正在分析HTML结构...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 输出页面标题
    title = soup.title.text if soup.title else "无标题"
    logger.info(f"页面标题: {title}")
    
    # 查找可能包含规则的容器
    main_containers = []
    for selector in ['main', '#content', '.content', '.rules-container', '.container', 'article']:
        containers = soup.select(selector)
        if containers:
            logger.info(f"找到 {len(containers)} 个可能的主要容器，使用选择器: '{selector}'")
            main_containers.extend(containers)
    
    if not main_containers:
        logger.info("未找到常见的主要容器，使用body作为容器")
        main_containers = [soup.body]
    
    return soup

def list_common_elements(soup):
    """列出页面中常见的元素类型和类名"""
    if not soup:
        return
        
    logger.info("页面中的主要HTML元素:")
    
    # 查找常见元素
    elements_to_check = ['div', 'article', 'section', 'li', 'card']
    class_counts = {}
    
    for elem_type in elements_to_check:
        elements = soup.find_all(elem_type)
        if elements:
            logger.info(f"- 找到 {len(elements)} 个 <{elem_type}> 元素")
            
            # 统计类名
            for elem in elements:
                if 'class' in elem.attrs:
                    for class_name in elem['class']:
                        if class_name in class_counts:
                            class_counts[class_name] += 1
                        else:
                            class_counts[class_name] = 1
    
    # 显示最常见的类名
    logger.info("\n最常见的CSS类名:")
    sorted_classes = sorted(class_counts.items(), key=lambda x: x[1], reverse=True)
    for class_name, count in sorted_classes[:10]:  # 只显示前10个
        logger.info(f"- .{class_name}: {count} 个元素")
    
    return sorted_classes

def test_selector(soup, selector):
    """测试CSS选择器并显示结果"""
    if not soup:
        return []
        
    elements = soup.select(selector)
    if not elements:
        logger.info(f"选择器 '{selector}' 未找到任何元素")
        return []
    
    logger.info(f"选择器 '{selector}' 找到 {len(elements)} 个元素")
    
    # 显示第一个元素的预览
    if elements:
        preview = str(elements[0]).replace('\n', ' ')[:200]
        logger.info(f"第一个元素预览: {preview}...")
        
        # 尝试提取一些常见属性
        if hasattr(elements[0], 'text'):
            logger.info(f"文本内容: {elements[0].text.strip()[:100]}...")
        
        # 显示子元素
        children = list(elements[0].children)
        child_elements = [c for c in children if hasattr(c, 'name') and c.name is not None]
        if child_elements:
            logger.info("子元素:")
            for i, child in enumerate(child_elements[:3]):  # 只显示前3个子元素
                logger.info(f"  {i+1}. <{child.name}> {child.attrs if hasattr(child, 'attrs') else ''}")
    
    return elements

def extract_with_selector(soup, card_selector, title_selector=None, desc_selector=None, content_selector=None):
    """使用自定义选择器提取规则"""
    if not soup:
        return []
        
    cards = soup.select(card_selector)
    if not cards:
        logger.error(f"未找到任何元素匹配卡片选择器: '{card_selector}'")
        return []
    
    logger.info(f"找到 {len(cards)} 个可能的规则卡片")
    rules = []
    
    for i, card in enumerate(cards):
        # 提取标题
        title = None
        if title_selector:
            title_elem = card.select_one(title_selector)
            title = title_elem.text.strip() if title_elem else None
        
        if not title:
            # 尝试常见的标题选择器
            for sel in ['h1', 'h2', 'h3', '.title', '.heading']:
                title_elem = card.select_one(sel)
                if title_elem:
                    title = title_elem.text.strip()
                    break
        
        if not title:
            title = f"规则 {i+1}"
        
        # 提取描述
        description = None
        if desc_selector:
            desc_elem = card.select_one(desc_selector)
            description = desc_elem.text.strip() if desc_elem else None
        
        if not description:
            # 尝试常见的描述选择器
            for sel in ['p', '.description', '.desc', '.summary']:
                desc_elem = card.select_one(sel)
                if desc_elem:
                    description = desc_elem.text.strip()
                    break
        
        if not description:
            description = ""
        
        # 提取内容
        content = None
        if content_selector:
            content_elem = card.select_one(content_selector)
            content = content_elem.text.strip() if content_elem else None
        
        if not content:
            # 提取卡片的所有文本作为内容
            content = card.text.strip()
        
        # 添加到规则列表
        rule = {
            "title": title,
            "description": description,
            "content": content[:100] + "..." if len(content) > 100 else content,
            "full_content": content
        }
        
        rules.append(rule)
        logger.info(f"规则 {i+1}: {title}")
    
    return rules

def interactive_mode(html_content):
    """交互式模式，允许用户探索HTML结构和测试选择器"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    print("\n===== 交互式HTML探索模式 =====")
    print("这个模式让您可以探索网页结构并测试CSS选择器")
    
    # 列出常见元素
    class_counts = list_common_elements(soup)
    
    while True:
        print("\n可用命令:")
        print("1. test <selector> - 测试CSS选择器并显示结果")
        print("2. extract <card_selector> [title_selector] [desc_selector] [content_selector] - 使用自定义选择器提取规则")
        print("3. classes - 显示页面中最常见的CSS类")
        print("4. help - 显示帮助信息")
        print("5. quit - 退出交互模式")
        
        cmd = input("\n请输入命令: ").strip()
        
        if cmd.lower() == 'quit' or cmd.lower() == 'exit':
            break
        elif cmd.lower() == 'help':
            print("\n命令说明:")
            print("test <selector> - 测试CSS选择器，如 'test .card' 或 'test article.post'")
            print("extract <card> [title] [desc] [content] - 提取规则，如 'extract .card h2 p .content'")
            print("classes - 显示页面中最常见的CSS类名")
            print("quit - 退出交互模式")
        elif cmd.lower() == 'classes':
            print("\n最常见的CSS类名:")
            for class_name, count in class_counts[:15]:  # 显示前15个
                print(f"- .{class_name}: {count} 个元素")
        elif cmd.lower().startswith('test '):
            selector = cmd[5:].strip()
            if not selector:
                print("错误: 请提供要测试的CSS选择器")
                continue
                
            print(f"\n测试选择器: '{selector}'")
            elements = test_selector(soup, selector)
            
            if elements and len(elements) > 0:
                print(f"找到 {len(elements)} 个匹配元素")
                view_details = input("查看第一个元素的更多细节? (y/n): ").lower() == 'y'
                
                if view_details and elements:
                    elem = elements[0]
                    print("\n元素详情:")
                    print(f"标签: <{elem.name}>")
                    print(f"属性: {elem.attrs}")
                    
                    text = elem.text.strip()
                    print(f"文本内容: {text[:200]}..." if len(text) > 200 else f"文本内容: {text}")
                    
                    print("\n子元素:")
                    for i, child in enumerate([c for c in elem.children if hasattr(c, 'name') and c.name is not None]):
                        print(f"{i+1}. <{child.name}> {child.attrs if hasattr(child, 'attrs') else ''}")
                        if i >= 5:  # 限制显示前6个子元素
                            print("...更多子元素省略...")
                            break
        elif cmd.lower().startswith('extract '):
            parts = cmd[8:].strip().split()
            if not parts:
                print("错误: 请提供要提取的CSS选择器")
                continue
                
            card_selector = parts[0]
            title_selector = parts[1] if len(parts) > 1 else None
            desc_selector = parts[2] if len(parts) > 2 else None
            content_selector = parts[3] if len(parts) > 3 else None
            
            print(f"\n使用以下选择器提取规则:")
            print(f"卡片选择器: {card_selector}")
            if title_selector: print(f"标题选择器: {title_selector}")
            if desc_selector: print(f"描述选择器: {desc_selector}")
            if content_selector: print(f"内容选择器: {content_selector}")
            
            rules = extract_with_selector(soup, card_selector, title_selector, desc_selector, content_selector)
            
            if rules:
                print(f"\n成功提取 {len(rules)} 个规则:")
                for i, rule in enumerate(rules[:5]):  # 只显示前5个
                    print(f"{i+1}. {rule['title']}")
                    print(f"   描述: {rule['description'][:50]}..." if len(rule['description']) > 50 else f"   描述: {rule['description']}")
                    print(f"   内容: {rule['content']}")
                    print()
                
                if len(rules) > 5:
                    print(f"...还有 {len(rules) - 5} 个规则省略...")
                
                save_option = input("是否保存这些规则为JSON文件? (y/n): ").lower()
                if save_option == 'y':
                    file_name = input("请输入文件名 (默认: extracted_rules.json): ").strip() or "extracted_rules.json"
                    with open(file_name, 'w', encoding='utf-8') as f:
                        json.dump(rules, f, ensure_ascii=False, indent=2)
                    print(f"规则已保存到 {file_name}")
            else:
                print("未能提取任何规则")
        else:
            print("无效的命令，请输入'help'查看可用命令")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='交互式测试从Cursor Directory获取规则')
    parser.add_argument('--offline', '-o', help='使用离线HTML文件进行测试', default=None)
    parser.add_argument('--url', '-u', help='自定义URL，默认为Cursor Directory', default=CURSOR_DIRECTORY_URL)
    parser.add_argument('--interactive', '-i', action='store_true', help='启用交互模式')
    parser.add_argument('--selector', '-s', help='用于提取规则卡片的CSS选择器', default='.rule-card')
    args = parser.parse_args()
    
    logger.info("=== Cursor Directory 规则获取交互式测试脚本开始 ===")
    
    # 获取页面内容
    html_content = get_page_content(args.url, args.offline)
    if not html_content:
        logger.error("无法获取页面内容，测试终止")
        return
    
    if args.interactive:
        # 交互式模式
        interactive_mode(html_content)
    else:
        # 自动模式
        soup = explore_html_structure(html_content)
        list_common_elements(soup)
        
        logger.info(f"\n使用选择器 '{args.selector}' 测试规则提取:")
        cards = test_selector(soup, args.selector)
        
        if cards:
            rules = extract_with_selector(soup, args.selector)
            
            if rules:
                logger.info(f"\n成功提取 {len(rules)} 个规则")
                for i, rule in enumerate(rules):
                    logger.info(f"{i+1}. {rule['title']}")
            else:
                logger.error("未能提取任何规则")
        
    logger.info("=== 测试脚本结束 ===")

if __name__ == "__main__":
    main() 