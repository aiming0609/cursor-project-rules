/**
 * @description Cursor Project Rules Generator VSCode扩展的主入口
 * @author [你的名字]
 */

import * as vscode from 'vscode';
import { RulesWebViewProvider } from './webviewProvider';

/**
 * @description 检查AI模型配置并提示用户进行配置
 * @param context 扩展上下文，用于存储状态
 */
async function checkModelConfiguration(context: vscode.ExtensionContext): Promise<boolean> {
  const config = vscode.workspace.getConfiguration('cursor-rules');
  const modelUrl = config.get<string>('modelUrl');
  const apiKey = config.get<string>('apiKey');
  const modelName = config.get<string>('modelName');
  
  // 检查是否所有必要配置都已完成
  const isConfigured = !!modelUrl && !!apiKey && !!modelName;
  
  // 如果已配置完成，直接返回true
  if (isConfigured) {
    return true;
  }
  
  // 判断之前是否已经提示过用户
  const hasPrompted = context.globalState.get<boolean>('hasPromptedForModelConfig');
  if (hasPrompted) {
    // 即使之前提示过，但是配置仍未完成，每次使用功能时仍然需要提示
    const configureNow = '立即配置';
    const choice = await vscode.window.showInformationMessage(
      '请先完成AI模型配置后再使用此功能。需要配置：模型URL、API密钥和模型名称。',
      configureNow
    );
    
    if (choice === configureNow) {
      // 根据缺少的配置项导航到相应的设置页面
      if (!modelUrl) {
        vscode.commands.executeCommand('cursor-project-rules.configureModel');
      } else if (!apiKey) {
        vscode.commands.executeCommand('cursor-project-rules.configureAPIKey');
      } else {
        await vscode.commands.executeCommand(
          'workbench.action.openSettings',
          'cursor-rules.modelName'
        );
      }
    }
    
    return false;
  }
  
  // 首次提示，提供更详细的信息
  const configureNow = '立即配置';
  const remindLater = '不再提醒';
  const choice = await vscode.window.showInformationMessage(
    '请配置AI模型信息以使用规则生成功能。需要配置：模型URL、API密钥和模型名称。',
    configureNow,
    remindLater
  );
  
  if (choice === configureNow) {
    // 根据缺少的配置项导航到相应的设置页面
    if (!modelUrl) {
      vscode.commands.executeCommand('cursor-project-rules.configureModel');
    } else if (!apiKey) {
      vscode.commands.executeCommand('cursor-project-rules.configureAPIKey');
    } else {
      await vscode.commands.executeCommand(
        'workbench.action.openSettings',
        'cursor-rules.modelName'
      );
    }
  } else if (choice === remindLater) {
    // 记住用户选择不再提醒
    await context.globalState.update('hasPromptedForModelConfig', true);
  }
  
  return false;
}

/**
 * @description 打开设置页面配置模型URL
 */
async function openModelURLConfiguration() {
  await vscode.commands.executeCommand(
    'workbench.action.openSettings',
    'cursor-rules.modelUrl'
  );
}

/**
 * @description 打开设置页面配置API密钥
 */
async function openAPIKeyConfiguration() {
  await vscode.commands.executeCommand(
    'workbench.action.openSettings',
    'cursor-rules.apiKey'
  );
}

/**
 * @description 重置配置提示状态，使配置提示再次显示
 * @param context 扩展上下文
 */
async function resetConfigPrompt(context: vscode.ExtensionContext) {
  await context.globalState.update('hasPromptedForModelConfig', false);
  vscode.window.showInformationMessage('配置提示状态已重置，下次使用功能时将再次显示配置提示');
}

/**
 * @description 显示规则选择界面
 */
async function showRulesSelector() {
  try {
    // 首先检查是否在工作区中
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
      vscode.window.showErrorMessage('请先打开一个项目文件夹');
      return;
    }

    // 显示WebView
    await vscode.commands.executeCommand('cursor-rules-view.focus');
  } catch (error) {
    vscode.window.showErrorMessage(`显示规则选择界面时出错: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * @description 激活扩展时调用
 * @param context 扩展上下文
 */
export function activate(context: vscode.ExtensionContext) {
  console.log('Cursor Project Rules Generator 已激活');
  
  // 在扩展激活时检查模型配置
  setTimeout(() => {
    checkModelConfiguration(context);
  }, 2000); // 延迟2秒显示提示，让VSCode界面完全加载

  // 注册WebView提供者
  const rulesProvider = new RulesWebViewProvider(context.extensionUri);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider(
      'cursor-rules-view',
      rulesProvider
    )
  );

  // 注册命令：生成项目规则
  const generateRulesCommand = vscode.commands.registerCommand(
    'cursor-project-rules.generateRules',
    async () => {
      try {
        // 首先检查模型配置
        if (!await checkModelConfiguration(context)) {
          return;
        }
        
        // 显示规则选择界面
        await showRulesSelector();
      } catch (error) {
        vscode.window.showErrorMessage(`出错: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
  );
  
  // 注册命令：使用本地规则选择器（保留这个命令作为别名）
  const localRulesCommand = vscode.commands.registerCommand(
    'cursor-project-rules.localRules',
    () => vscode.commands.executeCommand('cursor-project-rules.generateRules')
  );
  
  // 注册命令：预览可用规则
  const previewRulesCommand = vscode.commands.registerCommand(
    'cursor-project-rules.previewRules',
    async () => {
      // 首先检查模型配置
      if (!await checkModelConfiguration(context)) {
        return;
      }
      
      // 创建并显示WebView
      const panel = vscode.window.createWebviewPanel(
        'cursorRulesPreview',
        'Cursor可用规则预览',
        vscode.ViewColumn.One,
        {
          enableScripts: true,
          retainContextWhenHidden: true
        }
      );
      
      // 设置WebView内容
      panel.webview.html = getPreviewWebviewContent(panel.webview, context.extensionUri);
      
      // 处理WebView消息
      panel.webview.onDidReceiveMessage(
        (message: any) => {
          switch (message.command) {
            case 'applyRules':
              vscode.commands.executeCommand('cursor-project-rules.generateRules');
              return;
          }
        },
        undefined,
        context.subscriptions
      );
    }
  );
  
  // 注册命令：配置AI模型URL
  const configureModelCommand = vscode.commands.registerCommand(
    'cursor-project-rules.configureModel',
    openModelURLConfiguration
  );

  // 注册命令：配置API密钥（新增）
  const configureAPIKeyCommand = vscode.commands.registerCommand(
    'cursor-project-rules.configureAPIKey',
    openAPIKeyConfiguration
  );

  // 注册命令：重置配置提示状态
  const resetConfigPromptCommand = vscode.commands.registerCommand(
    'cursor-project-rules.resetConfigPrompt',
    () => resetConfigPrompt(context)
  );

  context.subscriptions.push(generateRulesCommand, previewRulesCommand, configureModelCommand, configureAPIKeyCommand, resetConfigPromptCommand, localRulesCommand);
}

/**
 * @description 获取规则预览WebView的HTML内容
 * @param webview Webview对象
 * @param extensionUri 扩展URI
 * @returns HTML内容
 */
function getPreviewWebviewContent(webview: vscode.Webview, extensionUri: vscode.Uri): string {
  // 获取资源路径
  const scriptUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'extension', 'webview', 'main.js'));
  const styleUri = webview.asWebviewUri(vscode.Uri.joinPath(extensionUri, 'extension', 'webview', 'style.css'));
  
  return `<!DOCTYPE html>
  <html lang="zh-CN">
  <head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Cursor可用规则预览</title>
    <link href="${styleUri}" rel="stylesheet">
  </head>
  <body>
    <div class="container">
      <h1>Cursor可用规则</h1>
      <p>从Cursor Directory加载规则中...</p>
      <div id="rules-container"></div>
      <div class="actions">
        <button id="apply-button">应用选中的规则</button>
      </div>
    </div>
    <script src="${scriptUri}"></script>
  </body>
  </html>`;
}

/**
 * @description 停用扩展时调用
 */
export function deactivate() {
  console.log('Cursor Project Rules Generator 已停用');
} 