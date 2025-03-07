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
  private _getHtmlForWebview(webview: vscode.Webview): string {
    // 获取脚本和样式路径
    const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'extension', 'webview', 'main.js'));
    const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(this._extensionUri, 'extension', 'webview', 'style.css'));

    return `<!DOCTYPE html>
    <html lang="zh-CN">
    <head>
      <meta charset="UTF-8">
      <meta name="viewport" content="width=device-width, initial-scale=1.0">
      <meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src ${webview.cspSource}; script-src ${webview.cspSource};">
      <title>Cursor规则管理</title>
      <link href="${styleUri}" rel="stylesheet">
      <style>
        body {
          font-family: var(--vscode-font-family);
          color: var(--vscode-foreground);
          background-color: var(--vscode-editor-background);
          padding: 0;
          margin: 0;
        }
        .container {
          padding: 15px;
        }
        .header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 16px;
          border-bottom: 1px solid var(--vscode-panel-border);
          padding-bottom: 8px;
        }
        .header h2 {
          margin: 0;
        }
        .loading {
          display: none;
          text-align: center;
          margin: 20px 0;
        }
        .rules-list {
          margin-bottom: 16px;
          max-height: 400px;
          overflow-y: auto;
          border: 1px solid var(--vscode-panel-border);
          border-radius: 4px;
        }
        .rule-item {
          padding: 10px;
          border-bottom: 1px solid var(--vscode-panel-border);
          cursor: pointer;
          display: flex;
          align-items: center;
        }
        .rule-item:last-child {
          border-bottom: none;
        }
        .rule-item:hover {
          background-color: var(--vscode-list-hoverBackground);
        }
        .rule-item input[type="checkbox"] {
          margin-right: 10px;
        }
        .rule-title {
          font-weight: bold;
          margin-bottom: 4px;
        }
        .rule-description {
          font-size: 0.9em;
          opacity: 0.8;
          margin-bottom: 4px;
        }
        .actions {
          display: flex;
          justify-content: space-between;
          margin-top: 16px;
        }
        button {
          background-color: var(--vscode-button-background);
          color: var(--vscode-button-foreground);
          border: none;
          padding: 6px 12px;
          border-radius: 2px;
          cursor: pointer;
        }
        button:hover {
          background-color: var(--vscode-button-hoverBackground);
        }
        .empty-message {
          text-align: center;
          padding: 20px;
          color: var(--vscode-disabledForeground);
        }
        .empty-message.error {
          color: var(--vscode-errorForeground);
          background-color: var(--vscode-inputValidation-errorBackground);
          border: 1px solid var(--vscode-inputValidation-errorBorder);
          padding: 10px;
          margin-bottom: 10px;
          border-radius: 4px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <div class="header">
          <h2>可用规则</h2>
          <button id="refresh-button" title="刷新规则列表">刷新</button>
        </div>
        
        <div id="loading" class="loading">
          <p>加载规则中...</p>
        </div>
        
        <div id="rules-list" class="rules-list">
          <!-- 规则列表将在此动态生成 -->
        </div>
        
        <div class="actions">
          <button id="apply-button">应用所选规则</button>
        </div>
      </div>
      <script src="${scriptUri}"></script>
    </body>
    </html>`;
  }
} 