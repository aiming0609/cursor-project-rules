#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
@description 测试从Cursor Directory获取规则的独立脚本
"""

import os
import sys
import json
import logging
import requests
import time
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

def test_connection():
    """测试与Cursor Directory的连接"""
    logger.info(f"正在测试连接: {CURSOR_DIRECTORY_URL}")
    try:
        response = requests.head(
            CURSOR_DIRECTORY_URL,
            timeout=10,
            allow_redirects=True,  # 允许跟踪重定向
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        logger.info(f"连接状态码: {response.status_code}")
        if response.history:
            logger.info(f"请求被重定向: {len(response.history)} 次")
            for i, resp in enumerate(response.history):
                logger.info(f"重定向 {i+1}: {resp.url} -> {resp.headers.get('Location')}")
            logger.info(f"最终URL: {response.url}")
        
        return response.status_code < 400  # 返回任何非4xx/5xx状态码
    except Exception as e:
        logger.error(f"连接测试失败: {str(e)}")
        return False

def fetch_page_content(save_html=True):
    """获取页面内容并可选择保存HTML"""
    logger.info(f"正在获取页面内容: {CURSOR_DIRECTORY_URL}")
    try:
        response = requests.get(
            CURSOR_DIRECTORY_URL, 
            timeout=15,
            allow_redirects=True,  # 允许跟踪重定向
            headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        )
        
        if response.status_code >= 400:
            logger.error(f"获取页面失败，HTTP状态码: {response.status_code}")
            return None
        
        # 显示重定向信息
        if response.history:
            logger.info(f"请求被重定向: {len(response.history)} 次")
            logger.info(f"最终URL: {response.url}")
            
        content = response.text
        logger.info(f"成功获取页面内容，长度: {len(content)} 字节")
        
        # 保存HTML以便分析
        if save_html:
            with open("cursor_directory.html", "w", encoding="utf-8") as f:
                f.write(content)
            logger.info(f"页面内容已保存到: cursor_directory.html")
            
        return content
    except Exception as e:
        logger.error(f"获取页面内容时出错: {str(e)}")
        return None

def analyze_html_structure(html_content):
    """分析HTML结构"""
    if not html_content:
        logger.error("没有HTML内容可分析")
        return
        
    logger.info("正在分析HTML结构...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 输出页面标题
    title = soup.title.text if soup.title else "无标题"
    logger.info(f"页面标题: {title}")
    
    # 尝试多种可能的CSS选择器来查找规则卡片
    selectors = [
        '.rule-card',                   # 原始选择器
        '.card', '.rule', '.rules-card',  # 常见替代选择器
        'article', '.post', '.item'      # 更通用的选择器
    ]
    
    for selector in selectors:
        elements = soup.select(selector)
        if elements:
            logger.info(f"使用选择器 '{selector}' 找到 {len(elements)} 个元素")
            # 打印第一个元素的结构示例
            if len(elements) > 0:
                logger.info(f"第一个元素示例:\n{elements[0][:200]}...")
        else:
            logger.info(f"选择器 '{selector}' 未找到任何元素")
    
    # 检查页面结构
    logger.info("页面主要结构:")
    for child in soup.body.children:
        if child.name:
            logger.info(f"- <{child.name}> 标签 (类: {child.get('class', '无')})")

def extract_rule_cards(html_content):
    """提取并解析规则卡片"""
    if not html_content:
        logger.error("没有HTML内容可解析")
        return []
        
    logger.info("尝试提取规则卡片...")
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 尝试不同的选择器
    rule_cards = soup.select('.rule-card')
    if not rule_cards:
        logger.warning("未找到'.rule-card'元素，尝试其他选择器...")
        
        # 尝试其他可能的选择器
        for selector in ['.card', '.rule', 'article.rule', '.rules-item']:
            rule_cards = soup.select(selector)
            if rule_cards:
                logger.info(f"使用选择器 '{selector}' 找到 {len(rule_cards)} 个可能的规则卡片")
                break
    
    if not rule_cards:
        logger.error("无法找到任何可能的规则卡片元素")
        return []
    
    logger.info(f"找到 {len(rule_cards)} 个可能的规则卡片")
    rules = []
    
    for i, card in enumerate(rule_cards):
        logger.info(f"正在解析第 {i+1} 个规则卡片...")
        
        # 尝试提取标题
        title_elem = card.select_one('.rule-title')
        if not title_elem:
            title_elem = card.select_one('h2') or card.select_one('h3') or card.select_one('.title')
        
        title = title_elem.text.strip() if title_elem else f"未知规则 {i+1}"
        
        # 尝试提取描述
        desc_elem = card.select_one('.rule-description')
        if not desc_elem:
            desc_elem = card.select_one('p') or card.select_one('.description')
        
        description = desc_elem.text.strip() if desc_elem else ""
        
        # 尝试提取内容
        content_elem = card.select_one('.rule-content')
        if not content_elem:
            content_elem = card.select_one('.content') or card
        
        content = content_elem.text.strip() if content_elem else ""
        
        # 添加到规则列表
        rule = {
            "title": title,
            "description": description,
            "content": content[:100] + "..." if len(content) > 100 else content
        }
        
        rules.append(rule)
        logger.info(f"规则 {i+1}: {title}")
    
    return rules

def main():
    """主函数"""
    logger.info("=== Cursor Directory 规则获取测试脚本开始 ===")
    
    # 测试连接
    if not test_connection():
        logger.error("连接测试失败，无法继续")
        return
    
    # 获取页面内容
    html_content = fetch_page_content()
    if not html_content:
        logger.error("无法获取页面内容，测试终止")
        return
    
    # 分析HTML结构
    analyze_html_structure(html_content)
    
    # 提取规则卡片
    rules = extract_rule_cards(html_content)
    
    # 输出结果
    if rules:
        logger.info(f"成功提取 {len(rules)} 个规则")
        logger.info("规则列表:")
        for i, rule in enumerate(rules):
            logger.info(f"{i+1}. {rule['title']}")
    else:
        logger.error("未能提取任何规则")
        
    logger.info("=== 测试脚本结束 ===")

if __name__ == "__main__":
    main() 