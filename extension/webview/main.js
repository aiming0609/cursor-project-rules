/**
 * @description WebView的前端JavaScript文件
 */

// 获取VS Code API
const vscode = acquireVsCodeApi();

// 存储规则数据
let rules = [];
let selectedRuleIds = [];

// DOM元素
const rulesListElement = document.getElementById('rules-list');
const loadingElement = document.getElementById('loading');
const applyButton = document.getElementById('apply-button');
const refreshButton = document.getElementById('refresh-button');

/**
 * @description 初始化页面
 */
function init() {
  // 注册按钮事件
  if (applyButton) {
    applyButton.addEventListener('click', () => {
      vscode.postMessage({
        command: 'applyRules',
        ruleIds: selectedRuleIds
      });
    });
  }

  if (refreshButton) {
    refreshButton.addEventListener('click', () => {
      setLoading(true);
      vscode.postMessage({
        command: 'refreshRules'
      });
    });
  }

  // 请求规则数据
  vscode.postMessage({
    command: 'refreshRules'
  });
}

/**
 * @description 设置加载状态
 * @param {boolean} isLoading - 是否正在加载
 */
function setLoading(isLoading) {
  if (loadingElement) {
    loadingElement.style.display = isLoading ? 'block' : 'none';
  }
  
  if (rulesListElement) {
    rulesListElement.style.opacity = isLoading ? '0.5' : '1';
  }
}

/**
 * @description 更新规则列表
 * @param {Array} newRules - 新的规则列表
 */
function updateRulesList(newRules) {
  rules = newRules;
  selectedRuleIds = [];
  
  if (!rulesListElement) {
    return;
  }
  
  // 清空列表
  rulesListElement.innerHTML = '';
  
  if (rules.length === 0) {
    rulesListElement.innerHTML = '<div class="empty-message">没有可用的规则</div>';
    return;
  }
  
  // 创建规则项
  rules.forEach(rule => {
    const ruleElement = document.createElement('div');
    ruleElement.className = 'rule-item';
    ruleElement.id = `rule-item-${rule.id}`;
    
    // 创建复选框
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `checkbox-${rule.id}`;
    checkbox.addEventListener('change', (e) => {
      if (e.target.checked) {
        selectedRuleIds.push(rule.id);
      } else {
        selectedRuleIds = selectedRuleIds.filter(id => id !== rule.id);
      }
    });
    
    // 创建标题
    const title = document.createElement('div');
    title.className = 'rule-title';
    title.textContent = rule.name;
    
    // 创建描述
    const description = document.createElement('div');
    description.className = 'rule-description';
    description.textContent = rule.description;
    
    // 创建作者
    const author = document.createElement('div');
    author.className = 'rule-author';
    author.textContent = `作者: ${rule.author}`;
    
    // 添加元素
    ruleElement.appendChild(checkbox);
    ruleElement.appendChild(title);
    ruleElement.appendChild(description);
    ruleElement.appendChild(author);
    
    // 添加点击事件（除了复选框）
    ruleElement.addEventListener('click', (e) => {
      if (e.target !== checkbox) {
        // 切换展开状态
        ruleElement.classList.toggle('expanded');
        
        // 如果是展开状态，显示内容
        if (ruleElement.classList.contains('expanded')) {
          // 检查是否已有内容元素
          if (!ruleElement.querySelector('.rule-content')) {
            const content = document.createElement('div');
            content.className = 'rule-content';
            content.textContent = rule.content;
            ruleElement.appendChild(content);
          }
        }
      }
    });
    
    rulesListElement.appendChild(ruleElement);
  });
}

/**
 * @description 处理来自扩展的消息
 */
window.addEventListener('message', event => {
  const message = event.data;
  
  switch (message.command) {
    case 'updateRules':
      updateRulesList(message.rules);
      break;
    case 'setLoading':
      setLoading(message.value);
      break;
  }
});

// 初始化页面
document.addEventListener('DOMContentLoaded', init); 