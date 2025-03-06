/**
 * @description WebView提供者，用于规则预览和管理
 */

import * as cp from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';

/**
 * @description 规则信息接口
 */
interface RuleInfo {
  id: string;
  name: string;
  title: string;
  description: string;
  content: string;
  tags?: string[];
  slug?: string;
}

/**
 * @description 规则WebView提供者类
 */
export class RulesWebViewProvider implements vscode.WebviewViewProvider {
  public static readonly viewType = 'cursor-rules-view';
  private _view?: vscode.WebviewView;

  /**
   * @description 构造函数
   * @param _extensionUri 扩展URI
   */
  constructor(private readonly _extensionUri: vscode.Uri) {}

  /**
   * @description 从本地JSON文件加载规则
   * @returns 规则列表
   */
  private async loadRulesFromJson(): Promise<RuleInfo[]> {
    try {
      const extensionPath = this._extensionUri.fsPath;
      const rulesJsonPath = path.join(extensionPath, 'rules_data', 'rules.db.json');
      
      if (!fs.existsSync(rulesJsonPath)) {
        throw new Error(`找不到规则数据文件: ${rulesJsonPath}`);
      }
      
      const rawData = fs.readFileSync(rulesJsonPath, 'utf8');
      const rulesData = JSON.parse(rawData);
      
      const rules: RuleInfo[] = rulesData.map((rule: any, index: number) => {
        return {
          id: rule.slug || `rule-${index}`,
          name: rule.slug ? `${rule.slug}-practices` : `rule-${index}`,
          title: rule.title || '未命名规则',
          description: rule.content?.substring(0, 100) + '...' || '无描述',
          content: rule.content || '',
          tags: rule.tags || [],
          slug: rule.slug || ''
        };
      });
      
      return rules;
    } catch (error) {
      console.error('加载规则失败:', error);
      vscode.window.showErrorMessage(`加载本地规则数据失败: ${error instanceof Error ? error.message : String(error)}`);
      return [];
    }
  }

  /**
   * @description 解析WebView
   * @param webviewView WebView视图
   * @param _context 上下文
   * @param _token 取消令牌
   */
  public async resolveWebviewView(
    webviewView: vscode.WebviewView,
    _context: vscode.WebviewViewResolveContext,
    _token: vscode.CancellationToken
  ): Promise<void> {
    this._view = webviewView;
    
    webviewView.webview.options = {
      enableScripts: true,
      localResourceRoots: [this._extensionUri]
    };
    
    webviewView.webview.html = this._getHtmlForWebview(webviewView.webview);
    
    // 获取规则并发送到WebView
    this.updateRulesList();
    
    // 处理来自WebView的消息
    webviewView.webview.onDidReceiveMessage(
      (message: any) => {
        switch (message.command) {
          case 'generateRule':
            if (message.ruleId) {
              this._generateSingleRule(message.ruleId);
            } else {
              vscode.window.showInformationMessage('请选择一个规则');
            }
            return;
          case 'refreshRules':
            this.updateRulesList();
            return;
        }
      },
      undefined,
      []
    );
  }

  /**
   * @description 更新规则列表
   */
  private async updateRulesList(): Promise<void> {
    if (!this._view) {
      return;
    }
    
    // 显示加载状态
    this._view.webview.postMessage({ command: 'setLoading', value: true });
    
    try {
      const rules = await this.loadRulesFromJson();
      this._view.webview.postMessage({ command: 'updateRules', rules });
    } catch (error) {
      vscode.window.showErrorMessage(`更新规则列表失败: ${error instanceof Error ? error.message : String(error)}`);
    } finally {
      this._view.webview.postMessage({ command: 'setLoading', value: false });
    }
  }

  /**
   * @description 生成单个规则
   * @param ruleId 规则ID
   */
  private async _generateSingleRule(ruleId: string): Promise<void> {
    try {
      // 检查是否在工作区中
      if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
        vscode.window.showErrorMessage('请先打开一个项目文件夹');
        return;
      }

      // 获取Python脚本的路径
      const extensionPath = this._extensionUri.fsPath;
      const scriptPath = path.join(extensionPath, 'scripts', 'local_rules_selector.py');
      
      // 获取工作区根路径
      const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
      
      // 创建输出通道
      const outputChannel = vscode.window.createOutputChannel('Cursor Rules Generator');
      outputChannel.show();
      outputChannel.appendLine(`开始生成规则: ${ruleId}`);
      
      // 获取配置项
      const config = vscode.workspace.getConfiguration('cursor-rules');
      const pythonPath = config.get<string>('pythonPath') || 'python';
      
      // 设置规则数据文件路径
      const rulesJsonPath = path.join(extensionPath, 'rules_data', 'rules.db.json');
      
      // 运行Python脚本并传递参数
      const childProcess = cp.spawn(pythonPath, [
        scriptPath, 
        workspacePath,
        '--rules-json', rulesJsonPath,
        '--selected-rule', ruleId
      ]);
      
      childProcess.stdout.on('data', (data: Buffer) => {
        outputChannel.append(data.toString());
      });
      
      childProcess.stderr.on('data', (data: Buffer) => {
        outputChannel.append(data.toString());
      });
      
      childProcess.on('close', (code: number) => {
        if (code === 0) {
          outputChannel.appendLine('规则生成完成！');
          vscode.window.showInformationMessage(`规则 ${ruleId} 已成功生成`);
        } else {
          outputChannel.appendLine(`进程退出，退出码: ${code}`);
          vscode.window.showErrorMessage('生成规则时出错');
        }
      });
    } catch (error) {
      vscode.window.showErrorMessage(`出错: ${error instanceof Error ? error.message : String(error)}`);
    }
  }

  /**
   * @description 获取WebView的HTML内容
   * @param webview WebView对象
   * @returns HTML内容
   */
  private _getHtmlForWebview(_webview: vscode.Webview): string {
    return `<!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <title>Cursor规则管理</title>
      <style>
        body {
          font-family: var(--vscode-font-family);
          color: var(--vscode-foreground);
          background-color: var(--vscode-editor-background);
          padding: 0;
          margin: 0;
        }
        .container {
          padding: 10px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 10px;
        }
        .header h2 {
          margin: 0;
        }
        .loading {
          text-align: center;
          padding: 20px;
          display: none;
        }
        .rules-list {
          max-height: 500px;
          overflow-y: auto;
        }
        .rule-item {
          padding: 8px;
          margin-bottom: 4px;
          border-radius: 4px;
          cursor: pointer;
          transition: background-color 0.2s;
        }
        .rule-item:hover {
          background-color: var(--vscode-list-hoverBackground);
        }
        .rule-item.selected {
          background-color: var(--vscode-list-activeSelectionBackground);
          color: var(--vscode-list-activeSelectionForeground);
        }
        .search-bar {
          margin-bottom: 10px;
          width: 100%;
          padding: 6px;
        }
        .rule-title {
          font-weight: bold;
        }
        .rule-tags {
          font-size: 0.8em;
          color: var(--vscode-descriptionForeground);
          margin-top: 4px;
        }
        .rule-description {
          margin-top: 4px;
          font-size: 0.9em;
        }
        button {
          background-color: var(--vscode-button-background);
          color: var(--vscode-button-foreground);
          border: none;
          padding: 5px 10px;
          cursor: pointer;
          border-radius: 2px;
        }
        button:hover {
          background-color: var(--vscode-button-hoverBackground);
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2>Cursor可用规则</h2>
          <button id="refresh-button">刷新</button>
        </div>
        <input type="text" id="search-input" class="search-bar" placeholder="搜索规则...">
        <div id="loading" class="loading">加载中...</div>
        <div id="rules-list" class="rules-list"></div>
      </div>
      <script>
        (function() {
          const vscode = acquireVsCodeApi();
          let rules = [];
          let selectedRuleId = null;
          
          // 元素引用
          const loadingElement = document.getElementById('loading');
          const rulesListElement = document.getElementById('rules-list');
          const refreshButton = document.getElementById('refresh-button');
          const searchInput = document.getElementById('search-input');
          
          // 初始化时隐藏加载提示
          loadingElement.style.display = 'none';
          
          // 渲染规则列表
          function renderRulesList(rules) {
            rulesListElement.innerHTML = '';
            
            if (rules.length === 0) {
              rulesListElement.innerHTML = '<div class="no-rules">没有找到规则</div>';
              return;
            }
            
            rules.forEach(rule => {
              const ruleElement = document.createElement('div');
              ruleElement.className = 'rule-item';
              ruleElement.setAttribute('data-id', rule.id);
              ruleElement.setAttribute('title', '点击生成这个规则');
              
              const titleElement = document.createElement('div');
              titleElement.className = 'rule-title';
              titleElement.textContent = rule.title;
              ruleElement.appendChild(titleElement);
              
              if (rule.tags && rule.tags.length > 0) {
                const tagsElement = document.createElement('div');
                tagsElement.className = 'rule-tags';
                tagsElement.textContent = '标签: ' + rule.tags.join(', ');
                ruleElement.appendChild(tagsElement);
              }
              
              const descElement = document.createElement('div');
              descElement.className = 'rule-description';
              descElement.textContent = rule.description;
              ruleElement.appendChild(descElement);
              
              ruleElement.addEventListener('click', () => {
                // 点击即生成这个规则
                vscode.postMessage({
                  command: 'generateRule',
                  ruleId: rule.id
                });
                
                // 取消之前的选中状态
                const previousSelected = document.querySelector('.rule-item.selected');
                if (previousSelected) {
                  previousSelected.classList.remove('selected');
                }
                
                // 设置新的选中状态
                ruleElement.classList.add('selected');
                selectedRuleId = rule.id;
              });
              
              rulesListElement.appendChild(ruleElement);
            });
          }
          
          // 过滤规则
          function filterRules(searchText) {
            if (!searchText) {
              return rules;
            }
            
            const lowerSearchText = searchText.toLowerCase();
            return rules.filter(rule => {
              return (
                rule.title.toLowerCase().includes(lowerSearchText) ||
                rule.description.toLowerCase().includes(lowerSearchText) ||
                (rule.tags && rule.tags.some(tag => tag.toLowerCase().includes(lowerSearchText)))
              );
            });
          }
          
          // 监听搜索输入
          searchInput.addEventListener('input', () => {
            const searchText = searchInput.value;
            const filteredRules = filterRules(searchText);
            renderRulesList(filteredRules);
          });
          
          // 监听刷新按钮
          refreshButton.addEventListener('click', () => {
            vscode.postMessage({ command: 'refreshRules' });
          });
          
          // 监听来自扩展的消息
          window.addEventListener('message', event => {
            const message = event.data;
            
            switch (message.command) {
              case 'updateRules':
                rules = message.rules;
                renderRulesList(rules);
                break;
              case 'setLoading':
                loadingElement.style.display = message.value ? 'block' : 'none';
                break;
            }
          });
          
          // 初始加载时请求规则
          vscode.postMessage({ command: 'refreshRules' });
        }())
      </script>
    </body>
    </html>`;
  }
} 