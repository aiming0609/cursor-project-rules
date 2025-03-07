/**
 * @description Cursor Project Rules Generator VSCode扩展的主入口
 * @author [你的名字]
 */

import * as cp from 'child_process';
import * as fs from 'fs';
import * as path from 'path';
import * as vscode from 'vscode';
import { RulesWebViewProvider } from './webviewProvider';

/**
 * @description 检查AI模型配置并提示用户进行配置
 */
async function checkModelConfiguration(): Promise<boolean> {
  const config = vscode.workspace.getConfiguration('cursor-rules');
  const modelUrl = config.get<string>('modelUrl');
  const apiKey = config.get<string>('apiKey');
  const modelName = config.get<string>('modelName');
  
  // 检查是否所有必要配置都已完成
  const isConfigured = !!modelUrl && !!apiKey && !!modelName;
  
  // 尝试验证URL格式
  let urlValid = false;
  let apiKeyValid = false;
  let modelNameValid = false;
  
  if (modelUrl) {
    try {
      const url = new URL(modelUrl);
      urlValid = url.protocol === 'http:' || url.protocol === 'https:';
    } catch (e) {
      urlValid = false;
    }
  }
  
  // 简单检查API密钥是否看起来合理
  if (apiKey) {
    apiKeyValid = apiKey.length > 8; // 大多数API密钥至少有8个字符
  }
  
  // 检查模型名称是否不为空
  if (modelName) {
    modelNameValid = modelName.trim().length > 0;
  }
  
  // 如果已配置完成且格式有效，直接返回true
  if (isConfigured && urlValid && apiKeyValid && modelNameValid) {
    return true;
  }
  
  // 创建提示消息
  let message = '请配置AI模型信息后再使用此功能。';
  
  if (!modelUrl) {
    message += '\n● 缺少模型URL。';
  } else if (!urlValid) {
    message += '\n● 模型URL格式无效，应为有效的http/https URL。';
  }
  
  if (!apiKey) {
    message += '\n● 缺少API密钥。';
  } else if (!apiKeyValid) {
    message += '\n● API密钥可能无效，长度太短。';
  }
  
  if (!modelName) {
    message += '\n● 缺少模型名称。';
  }
  
  // 显示配置提示
  const configureNow = '立即配置';
  const choice = await vscode.window.showInformationMessage(
    message,
    configureNow
  );
  
  if (choice === configureNow) {
    // 打开设置页面进行配置
    if (!modelUrl || !urlValid) {
      // 如果URL缺失或无效，优先配置URL
      vscode.commands.executeCommand('cursor-project-rules.configureModel');
    } else if (!apiKey || !apiKeyValid) {
      // 如果API密钥缺失或无效，其次配置API密钥
      vscode.commands.executeCommand('cursor-project-rules.configureAPIKey');
    } else {
      // 最后配置模型名称
      await vscode.commands.executeCommand(
        'workbench.action.openSettings',
        'cursor-rules.modelName'
      );
    }
  }
  
  return false;  // 配置未完成
}

/**
 * @description 打开设置页面配置模型URL
 */
async function openModelURLConfiguration() {
  // 首先显示说明文档
  const modelUrlInfo = '请输入AI模型的API URL地址。\n\n' +
                      '对于OpenAI，通常是: https://api.openai.com/v1/chat/completions\n' +
                      '对于Azure OpenAI，通常是: https://your-resource-name.openai.azure.com/openai/deployments/your-deployment-name/chat/completions?api-version=2023-05-15\n' +
                      '对于其他模型提供商，请参考其API文档。';
  
  await vscode.window.showInformationMessage(modelUrlInfo);
  
  // 然后打开设置页面
  await vscode.commands.executeCommand(
    'workbench.action.openSettings',
    'cursor-rules.modelUrl'
  );
}

/**
 * @description 打开设置页面配置API密钥
 */
async function openAPIKeyConfiguration() {
  // 首先显示说明文档
  const apiKeyInfo = '请输入AI模型服务的API密钥。\n\n' +
                    '对于OpenAI，密钥格式通常以"sk-"开头，后面跟一串字母数字。\n' +
                    '对于Azure OpenAI，密钥格式通常是一串字母数字。\n' +
                    '请确保您的API密钥有足够的权限访问模型。';
  
  await vscode.window.showInformationMessage(apiKeyInfo);
  
  // 然后打开设置页面
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
 * @description 规则QuickPick项目接口
 */
interface RuleQuickPickItem extends vscode.QuickPickItem {
  id: string;
  slug: string;
}

/**
 * @description 显示规则选择界面
 * @param context 扩展上下文
 */
async function showRulesSelector(context: vscode.ExtensionContext) {
  try {
    // 首先检查是否在工作区中
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
      vscode.window.showErrorMessage('请先打开一个项目文件夹');
      return;
    }
    
    // 必须配置模型，不提供跳过选项
    if (!await checkModelConfiguration()) {
      return;
    }

    // 使用扩展上下文获取路径
    const extensionUri = context.extensionUri;
    const extensionPath = extensionUri.fsPath;
    
    const rulesJsonPath = path.join(extensionPath, 'rules_data', 'rules.db.json');
    let rules: RuleQuickPickItem[] = [];

    try {
      if (fs.existsSync(rulesJsonPath)) {
        const rawData = fs.readFileSync(rulesJsonPath, 'utf8');
        const rulesData = JSON.parse(rawData);
        
        rules = rulesData.map((rule: any, index: number) => {
          // 获取规则类型（从slug中提取）
          const ruleType = getRuleTypeFromSlug(rule.slug || '');
          
          return {
            id: rule.slug || `rule-${index}`,
            label: rule.title || '未命名规则',
            // 显示友好的规则类型名称
            description: ruleType,
            // 在detail中显示简短说明，不包含具体内容
            detail: '',
            slug: rule.slug || ''
          };
        });
        
        // 按照类型排序规则
        rules.sort((a, b) => {
          const descA = a.description || '';
          const descB = b.description || '';
          return descA.localeCompare(descB);
        });
      } else {
        vscode.window.showErrorMessage(`找不到规则数据文件: ${rulesJsonPath}`);
        return;
      }
    } catch (error) {
      vscode.window.showErrorMessage(`加载规则数据失败: ${error instanceof Error ? error.message : String(error)}`);
      return;
    }

    // 显示QuickPick列表让用户选择规则
    const selectedRule = await vscode.window.showQuickPick(rules, {
      placeHolder: '选择一个规则',
      ignoreFocusOut: true
    });

    if (selectedRule) {
      // 用户选择了规则，生成规则
      await generateSingleRule(selectedRule.id, extensionUri);
    }
  } catch (error) {
    vscode.window.showErrorMessage(`显示规则选择界面时出错: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * @description 生成单个规则
 * @param ruleId 规则ID
 * @param extensionUri 扩展URI
 */
async function generateSingleRule(ruleId: string, extensionUri: vscode.Uri): Promise<void> {
  try {
    // 检查是否在工作区中
    if (!vscode.workspace.workspaceFolders || vscode.workspace.workspaceFolders.length === 0) {
      vscode.window.showErrorMessage('请先打开一个项目文件夹');
      return;
    }
    
    // 获取工作区根路径和扩展路径
    const workspacePath = vscode.workspace.workspaceFolders[0].uri.fsPath;
    const extensionPath = extensionUri.fsPath;
    
    // 创建输出通道
    const outputChannel = vscode.window.createOutputChannel('Cursor Rules Generator');
    outputChannel.show();
    outputChannel.appendLine(`开始生成规则: ${ruleId}`);
    outputChannel.appendLine(`扩展路径: ${extensionPath}`);
    outputChannel.appendLine(`工作区路径: ${workspacePath}`);
    
    // 检查Python是否安装
    const pythonConfig = vscode.workspace.getConfiguration('cursor-rules');
    let pythonPath = pythonConfig.get<string>('pythonPath') || 'python';
    
    // 尝试检测Python解释器
    try {
      outputChannel.appendLine(`检查Python解释器: ${pythonPath}`);
      await checkPythonInterpreter(pythonPath, outputChannel);
    } catch (error) {
      // 如果指定的Python路径不可用，尝试其他常见路径
      outputChannel.appendLine(`指定的Python路径不可用: ${error instanceof Error ? error.message : String(error)}`);
      outputChannel.appendLine('尝试其他常见Python路径...');
      
      const commonPythonPaths = [
        'python3',
        'python',
        'py',
        'C:\\Python39\\python.exe',
        'C:\\Python38\\python.exe',
        'C:\\Python37\\python.exe',
        'C:\\Program Files\\Python39\\python.exe',
        'C:\\Program Files\\Python38\\python.exe',
        'C:\\Program Files\\Python37\\python.exe',
        'C:\\Program Files (x86)\\Python39\\python.exe',
        'C:\\Program Files (x86)\\Python38\\python.exe',
        'C:\\Program Files (x86)\\Python37\\python.exe'
      ];
      
      let pythonFound = false;
      for (const path of commonPythonPaths) {
        try {
          outputChannel.appendLine(`尝试Python路径: ${path}`);
          await checkPythonInterpreter(path, outputChannel);
          pythonPath = path;
          pythonFound = true;
          outputChannel.appendLine(`找到可用的Python解释器: ${pythonPath}`);
          break;
        } catch (e) {
          // 继续尝试下一个路径
        }
      }
      
      if (!pythonFound) {
        vscode.window.showErrorMessage('找不到可用的Python解释器，请在设置中配置正确的Python路径');
        return;
      }
    }
    
    // 尝试多个可能的Python脚本路径
    const possibleScriptPaths = [
      path.join(workspacePath, 'scripts', 'local_rules_selector.py'),
      path.join(extensionPath, 'scripts', 'local_rules_selector.py'),
      path.join(workspacePath, 'local_rules_selector.py'),
      path.join(__dirname, '..', '..', 'scripts', 'local_rules_selector.py'),
      path.join(__dirname, '..', 'scripts', 'local_rules_selector.py'),
    ];
    
    let scriptPath = '';
    for (const potentialPath of possibleScriptPaths) {
      outputChannel.appendLine(`检查脚本路径: ${potentialPath}`);
      if (fs.existsSync(potentialPath)) {
        scriptPath = potentialPath;
        outputChannel.appendLine(`找到脚本: ${scriptPath}`);
        break;
      }
    }
    
    if (!scriptPath) {
      // 如果所有路径都不存在，创建Python脚本
      scriptPath = path.join(workspacePath, 'scripts', 'local_rules_selector.py');
      outputChannel.appendLine(`未找到Python脚本，将创建: ${scriptPath}`);
      
      // 确保目录存在
      const scriptDir = path.dirname(scriptPath);
      if (!fs.existsSync(scriptDir)) {
        fs.mkdirSync(scriptDir, { recursive: true });
        outputChannel.appendLine(`创建目录: ${scriptDir}`);
      }
      
      // 从扩展中复制脚本
      const extensionScriptPath = path.join(extensionPath, 'scripts', 'local_rules_selector.py');
      if (fs.existsSync(extensionScriptPath)) {
        fs.copyFileSync(extensionScriptPath, scriptPath);
        outputChannel.appendLine(`从扩展复制脚本: ${extensionScriptPath} -> ${scriptPath}`);
      } else {
        vscode.window.showErrorMessage(`找不到Python脚本，请确保您的工作区中有scripts/local_rules_selector.py文件`);
        return;
      }
    }
    
    // 获取模型配置
    const config = vscode.workspace.getConfiguration('cursor-rules');
    const modelUrl = config.get<string>('modelUrl');
    const apiKey = config.get<string>('apiKey');
    const modelName = config.get<string>('modelName');
    
    // 设置规则数据文件路径（使用绝对路径）
    const rulesJsonPath = path.join(extensionPath, 'rules_data', 'rules.db.json');
    if (!fs.existsSync(rulesJsonPath)) {
      vscode.window.showErrorMessage(`找不到规则数据文件: ${rulesJsonPath}`);
      outputChannel.appendLine(`规则数据文件不存在: ${rulesJsonPath}`);
      return;
    }
    
    outputChannel.appendLine(`规则数据文件: ${rulesJsonPath}`);
    
    // 显示进度提示
    await vscode.window.withProgress(
      {
        location: vscode.ProgressLocation.Notification,
        title: `正在生成规则: ${ruleId}`,
        cancellable: false
      },
      async () => {
        return new Promise<void>((resolve, reject) => {
          // 设置环境变量以传递模型配置
          const env: {[key: string]: string} = {
            ...process.env,
            CURSOR_RULES_MODEL_URL: modelUrl || '',
            CURSOR_RULES_API_KEY: apiKey || '',
            CURSOR_RULES_MODEL_NAME: modelName || '',
            // 确保路径正确传递
            PYTHONPATH: [
              path.dirname(scriptPath),
              path.join(extensionPath, 'scripts'),
              process.env.PYTHONPATH || ''
            ].join(path.delimiter),
            // 设置Python I/O编码为UTF-8，解决中文乱码问题
            PYTHONIOENCODING: 'utf-8'
          };
          
          // 记录重要信息（安全起见，不记录API密钥）
          outputChannel.appendLine(`CURSOR_RULES_MODEL_URL环境变量: ${env.CURSOR_RULES_MODEL_URL}`);
          outputChannel.appendLine(`CURSOR_RULES_MODEL_NAME环境变量: ${env.CURSOR_RULES_MODEL_NAME}`);
          outputChannel.appendLine(`PYTHONPATH环境变量: ${env.PYTHONPATH}`);
          outputChannel.appendLine(`工作区路径: ${workspacePath}`);
          outputChannel.appendLine(`期望输出目录: ${path.join(workspacePath, '.cursor', 'rules')}`);

          // 在本地创建目录确保存在
          try {
            const rulesDir = path.join(workspacePath, '.cursor', 'rules');
            if (!fs.existsSync(rulesDir)) {
              fs.mkdirSync(rulesDir, { recursive: true });
              outputChannel.appendLine(`创建规则目录: ${rulesDir}`);
            } else {
              outputChannel.appendLine(`规则目录已存在: ${rulesDir}`);
            }
          } catch (error) {
            outputChannel.appendLine(`创建规则目录时出错: ${error instanceof Error ? error.message : String(error)}`);
          }
          
          const args = [
            scriptPath,
            workspacePath,  // 确保传递正确的工作区路径
            '--rules-json', rulesJsonPath,
            '--selected-rule', ruleId,
            '--debug',  // 添加调试参数
            '--output-dir', path.join(workspacePath, '.cursor', 'rules')
          ];
          
          outputChannel.appendLine(`执行命令: ${pythonPath} ${args.join(' ')}`);
          
          const childProcess = cp.spawn(pythonPath, args, { env, cwd: workspacePath });
          
          childProcess.stdout.on('data', (data: Buffer) => {
            outputChannel.append(data.toString());
          });
          
          childProcess.stderr.on('data', (data: Buffer) => {
            outputChannel.append(data.toString());
          });
          
          childProcess.on('error', (error) => {
            outputChannel.appendLine(`启动进程时出错: ${error.message}`);
            vscode.window.showErrorMessage(`启动Python进程失败: ${error.message}`);
            reject(error);
          });
          
          childProcess.on('close', (code: number) => {
            if (code === 0) {
              outputChannel.appendLine('规则生成完成！');
              
              // 检查规则文件是否实际创建
              const rulesDirPath = path.join(workspacePath, '.cursor', 'rules');
              if (fs.existsSync(rulesDirPath)) {
                const ruleFiles = fs.readdirSync(rulesDirPath);
                outputChannel.appendLine(`规则目录 ${rulesDirPath} 中的文件:`);
                if (ruleFiles.length > 0) {
                  ruleFiles.forEach(file => outputChannel.appendLine(`- ${file}`));
                  vscode.window.showInformationMessage(`规则 ${ruleId} 已成功生成`);
                } else {
                  outputChannel.appendLine('规则目录为空，没有生成规则文件');
                  vscode.window.showWarningMessage(`规则生成过程完成，但没有找到生成的规则文件`);
                }
              } else {
                outputChannel.appendLine(`规则目录 ${rulesDirPath} 不存在`);
                vscode.window.showWarningMessage(`规则生成过程完成，但规则目录不存在`);
              }
              
              resolve();
            } else {
              outputChannel.appendLine(`进程退出，退出码: ${code}`);
              vscode.window.showErrorMessage(`生成规则失败，退出码: ${code}，请查看输出面板了解详情`);
              reject(new Error(`进程退出，退出码: ${code}`));
            }
          });
        });
      }
    );
  } catch (error) {
    vscode.window.showErrorMessage(`出错: ${error instanceof Error ? error.message : String(error)}`);
  }
}

/**
 * @description 检查Python解释器是否可用
 * @param pythonPath Python解释器路径
 * @param outputChannel 输出通道
 */
async function checkPythonInterpreter(pythonPath: string, outputChannel: vscode.OutputChannel): Promise<void> {
  return new Promise<void>((resolve, reject) => {
    const process = cp.spawn(pythonPath, ['--version']);
    
    let output = '';
    process.stdout.on('data', (data) => {
      output += data.toString();
    });
    
    process.stderr.on('data', (data) => {
      output += data.toString();
    });
    
    process.on('error', (error) => {
      outputChannel.appendLine(`无法启动Python解释器 ${pythonPath}: ${error.message}`);
      reject(error);
    });
    
    process.on('close', (code) => {
      if (code === 0) {
        outputChannel.appendLine(`Python版本: ${output.trim()}`);
        resolve();
      } else {
        outputChannel.appendLine(`Python检查失败，退出码: ${code}`);
        reject(new Error(`Python检查失败，退出码: ${code}`));
      }
    });
  });
}

/**
 * @description 激活扩展时调用
 * @param context 扩展上下文
 */
export function activate(context: vscode.ExtensionContext) {
  console.log('Cursor Project Rules Generator 已激活');
  
  // 在扩展激活时检查模型配置
  setTimeout(() => {
    checkModelConfiguration();
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
        if (!await checkModelConfiguration()) {
          return;
        }
        
        // 显示规则选择界面
        await showRulesSelector(context);
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
      if (!await checkModelConfiguration()) {
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

/**
 * @description 从规则的slug中提取规则类型
 * @param slug 规则的slug
 * @returns 友好的规则类型名称
 */
function getRuleTypeFromSlug(slug: string): string {
  // 根据slug解析规则类型
  if (slug.includes('angular')) {
    return '📐 Angular';
  } else if (slug.includes('react')) {
    return '⚛️ React';
  } else if (slug.includes('vue')) {
    return '🟢 Vue';
  } else if (slug.includes('typescript') || slug.includes('ts')) {
    return '📘 TypeScript';
  } else if (slug.includes('javascript') || slug.includes('js')) {
    return '📙 JavaScript';
  } else if (slug.includes('python')) {
    return '🐍 Python';
  } else if (slug.includes('java')) {
    return '☕ Java';
  } else if (slug.includes('php')) {
    return '🐘 PHP';
  } else if (slug.includes('ruby')) {
    return '💎 Ruby';
  } else if (slug.includes('go')) {
    return '🔵 Go';
  } else if (slug.includes('rust')) {
    return '🦀 Rust';
  } else if (slug.includes('csharp') || slug.includes('cs') || slug.includes('dotnet')) {
    return '🟣 C#/.NET';
  } else if (slug.includes('c++') || slug.includes('cpp')) {
    return '🔴 C++';
  } else if (slug.includes('swift')) {
    return '🧡 Swift';
  } else if (slug.includes('kotlin')) {
    return '🟠 Kotlin';
  } else if (slug.includes('flutter')) {
    return '🦋 Flutter';
  } else if (slug.includes('data-science') || slug.includes('machine-learning')) {
    return '📊 数据科学';
  } else if (slug.includes('web')) {
    return '🌐 Web';
  } else if (slug.includes('mobile')) {
    return '📱 移动开发';
  } else if (slug.includes('devops')) {
    return '🔄 DevOps';
  } else if (slug.includes('database') || slug.includes('sql')) {
    return '💾 数据库';
  } else if (slug.includes('security')) {
    return '🔒 安全';
  } else if (slug.includes('test') || slug.includes('testing')) {
    return '🧪 测试';
  } else if (slug.includes('best-practices')) {
    return '✅ 最佳实践';
  } else if (slug.includes('guideline') || slug.includes('guidelines')) {
    return '📝 指南';
  } else {
    return '🔍 其他';
  }
}
