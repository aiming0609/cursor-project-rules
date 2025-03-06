# Cursor Project Rules Generator

这是一个VSCode插件，用于从[Cursor Directory](https://cursor.directory/rules/)获取规则，并将其转换为Cursor兼容的project rules格式。

## 功能特点

- 从Cursor Directory网站抓取最新规则
- 通过Python脚本转换规则为Cursor项目规则格式
- 在VSCode中提供友好的用户界面进行规则管理
- 支持规则预览、选择和应用
- 支持使用自定义AI模型生成规则
- 智能本地规则选择器，可分析项目结构并使用AI定制规则内容

## 项目结构

- `extension/` - VSCode扩展源代码
  - `src/` - TypeScript源文件（扩展主要逻辑）
  - `webview/` - 网页视图界面（前端界面）
- `scripts/` - Python转换脚本（规则获取和处理）
- `templates/` - 规则模板文件（用于生成规则）

## 安装步骤

1. 确保已安装以下依赖：
   - Node.js (>= 14.x)
   - Python (>= 3.8)
   - VSCode (>= 1.70.0)

2. 克隆仓库并安装依赖：
   ```bash
   git clone https://github.com/yourusername/cursor-project-rules.git
   cd cursor-project-rules
   npm install
   pip install -r scripts/requirements.txt
   ```

3. 编译扩展：
   ```bash
   npm run compile
   ```

4. 在VSCode中测试扩展：
   - 打开VSCode
   - 选择文件 > 打开文件夹，然后打开此项目
   - 按F5启动调试（或点击"运行和调试"，然后选择"运行扩展"）

## 使用方法

### 设置AI模型（必需步骤）

使用此插件前，必须完成AI模型配置：

1. 点击提示中的"立即配置"按钮或使用命令面板选择以下命令之一：
   - "Cursor: 配置AI模型URL" - 配置模型的API地址
   - "Cursor: 配置AI模型API密钥" - 配置访问API所需的密钥

2. 在打开的设置页面中，配置以下**所有**必要选项：
   - `cursor-rules.modelUrl`: AI模型API的URL地址（例如：https://api.openai.com/v1/chat/completions）
   - `cursor-rules.apiKey`: AI模型的API密钥
   - `cursor-rules.modelName`: 使用的AI模型名称

**重要说明**：必须配置上述所有三项才能使用插件功能。未完成配置时，每次使用功能将收到提示。

### 使用配置助手工具

我们提供了配置助手工具，帮助您更轻松地设置模型配置：

1. **Windows用户**：
   - 运行项目根目录下的 `configure_model.bat` 批处理文件
   - 按照提示输入所需的配置信息

2. **所有平台**：
   - 在终端中运行 `python scripts/configure_helper.py`
   - 按照提示输入配置信息

3. **使用环境变量**：
   - 设置以下环境变量后运行 `python scripts/configure_helper.py --batch`：
     - `CURSOR_RULES_MODEL_URL`: 模型API的URL地址
     - `CURSOR_RULES_API_KEY`: 模型的API密钥
     - `CURSOR_RULES_MODEL_NAME`: 使用的模型名称

### 配置提示重置

如果需要重新显示配置提示（例如需要更改为不同的模型服务）：

1. 打开命令面板（Ctrl+Shift+P或Cmd+Shift+P）
2. 输入并选择"Cursor: 重置配置提示状态"
3. 下次使用功能时将再次显示配置提示

### 生成项目规则

1. 在VSCode中打开您的项目
2. 打开命令面板（Ctrl+Shift+P或Cmd+Shift+P）
3. 输入并选择"Cursor: 生成Project Rules"
4. 等待扩展获取可用规则并生成项目规则
5. 规则将被保存在项目的`.cursor/rules/`目录中

### 使用本地规则选择器

本插件提供了一个强大的本地规则选择器功能，可以直接从本地规则数据库中选择规则，并通过AI模型对规则进行定制化处理：

1. **通过命令面板使用**：
   - 在VSCode中打开命令面板 (Ctrl+Shift+P)
   - 输入 "Cursor: 选择本地规则"
   - 从列表中选择需要的规则
   - 规则将自动通过AI模型进行分析和定制，基于项目的结构和技术栈

2. **通过批处理文件使用**：
   - 双击项目根目录下的 `select_local_rules.bat` 文件
   - 按提示选择规则
   - 系统将自动使用AI模型分析项目并定制规则内容

本地规则选择器的优势：
- **智能项目分析**：自动检测项目使用的技术栈和文件结构
- **AI驱动定制**：基于项目特点自动调整规则内容和匹配模式
- **离线备选方案**：当无法连接到Cursor Directory网站时，提供可靠的规则获取方式

注意：本地规则选择器需要配置AI模型才能发挥最佳效果。首次使用时，系统会提示您输入模型URL、API密钥和模型名称。您也可以通过环境变量预先配置这些信息：
```bash
# Windows (PowerShell)
$env:CURSOR_RULES_MODEL_URL="https://api.openai.com/v1/chat/completions"
$env:CURSOR_RULES_API_KEY="your-api-key"
$env:CURSOR_RULES_MODEL_NAME="gpt-3.5-turbo"

# Linux/macOS
export CURSOR_RULES_MODEL_URL="https://api.openai.com/v1/chat/completions"
export CURSOR_RULES_API_KEY="your-api-key"
export CURSOR_RULES_MODEL_NAME="gpt-3.5-turbo"
```

### 预览和选择规则

1. 在VSCode中打开命令面板
2. 输入并选择"Cursor: 预览可用规则"
3. 浏览并勾选想要应用的规则
4. 点击"应用选中的规则"按钮

## 配置选项

在VSCode设置中，可以配置以下选项：

- `cursor-rules.pythonPath`: Python解释器路径
  - 默认值: `python`
  - 如果您的Python环境不在默认路径，请指定完整路径
  
- `cursor-rules.autoSync`: 是否自动同步规则
  - 默认值: `false`
  - 设置为`true`时，每次打开项目会自动更新规则
  
- `cursor-rules.customTemplateDir`: 自定义模板目录
  - 默认值: 空
  - 如果需要使用自定义模板，指定目录路径
  
- `cursor-rules.modelUrl`: AI模型API的URL地址
  - 默认值: 空
  - 例如: `https://api.deepseek.com/v1/chat/completions` 或其他模型服务的URL
  
- `cursor-rules.apiKey`: AI模型的API密钥
  - 默认值: 空
  - 您需要从模型提供商获取API密钥

- `cursor-rules.modelName`: 使用的AI模型名称
  - 默认值: `deepseek-ai/DeepSeek-R1-Distill-Llama-8B`
  - 可根据实际使用的模型调整

## AI模型说明

本插件支持使用任何符合OpenAI API格式的模型服务，包括但不限于：

- OpenAI API (GPT-3.5, GPT-4等)
- DeepSeek
- Claude
- 本地部署的开源模型

默认使用DeepSeek模型，您可以根据需要替换为其他模型。模型需要支持生成规范格式的JSON输出。

## 规则格式说明

Cursor项目规则使用MDC（Markdown Configuration）格式，包含以下部分：

```
---
name: rule-name.mdc
description: 规则描述
globs: **/*.{ts,tsx}
---

- 这是第一条规则
- 这是第二条规则
- 这是第三条规则
```

- `name`: 规则文件名称（必须以.mdc结尾）
- `description`: 规则的简短描述
- `globs`: 文件匹配模式，决定规则适用于哪些文件
- 正文部分: 每行一条规则，以减号开头

## 开发指南

### 添加新功能

1. 修改TypeScript源代码：
   - `extension/src/extension.ts` - 插件主入口
   - `extension/src/webviewProvider.ts` - WebView提供者

2. 修改前端界面：
   - `extension/webview/main.js` - 前端脚本
   - `extension/webview/style.css` - 样式文件

3. 修改Python脚本：
   - `scripts/fetch_and_convert.py` - 规则获取和转换逻辑

### 编译和测试

```bash
# 编译TypeScript
npm run compile

# 持续监视并编译更改
npm run watch

# 运行扩展（在VSCode中）
按F5或从调试菜单启动
```

### 发布扩展

```bash
# 安装vsce工具
npm install -g vsce

# 创建VSIX包
vsce package

# 发布到VSCode Marketplace（需要有发布权限）
vsce publish
```

## 故障排除

1. **无法启动Python脚本**
   - 检查Python路径配置是否正确
   - 确保已安装所需的Python依赖

2. **无法获取规则**
   - 检查网络连接
   - Cursor Directory网站结构可能已变更，请使用测试工具分析网站结构

3. **无法调用AI模型**
   - 确认模型URL和API密钥配置正确
   - 检查网络连接是否可以访问模型服务
   - 查看输出日志中的详细错误信息

4. **生成的规则文件有问题**
   - 检查模板文件是否正确
   - 确保目标目录有写入权限

## 网站结构变更处理

如果Cursor Directory网站结构发生变化，导致无法正常获取规则，可以使用以下工具进行诊断和修复：

### 测试工具

1. **基本测试脚本**
   ```bash
   python scripts/test_fetch_rules.py
   ```
   此脚本会尝试连接网站并分析HTML结构，帮助诊断问题所在。

2. **交互式测试工具**
   ```bash
   python scripts/test_fetch_interactive.py --interactive
   ```
   此工具提供交互式界面，让您可以探索网页结构并测试不同的CSS选择器。

3. **批处理测试工具**
   ```bash
   .\test_website.bat
   ```
   Windows用户可以使用此批处理文件运行各种测试模式。

### 更新选择器

如果网站结构已变更，您可以使用以下工具更新主脚本中的CSS选择器：

1. **交互式更新选择器**
   ```bash
   python scripts/update_selectors.py
   ```
   此工具会引导您更新各种CSS选择器。

2. **从JSON文件更新选择器**
   ```bash
   python scripts/update_selectors.py --json selectors.json
   ```
   如果您已经有了一个包含新选择器的JSON文件，可以使用此命令直接更新。

### 推荐流程

1. 使用交互式测试工具探索网站结构
2. 找到有效的CSS选择器
3. 使用更新选择器工具更新主脚本
4. 测试更新后的脚本是否能正确获取规则

## 贡献指南

欢迎提交问题报告和贡献代码！请确保遵循以下准则：

1. 创建分支进行开发
2. 遵循现有代码风格
3. 提交前运行代码检查和测试
4. 提交清晰的PR描述

## 许可证

MIT 