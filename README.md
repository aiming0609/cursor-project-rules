# Cursor Project Rules Generator

这是一个VSCode插件，用于从本地规则库中选择规则，并通过AI模型定制为Cursor兼容的project rules格式。

## 功能特点

- 从本地规则库中选择适合的规则
- 使用AI模型根据项目特点定制规则内容
- 在VSCode中提供友好的用户界面进行规则管理
- 支持规则预览、选择和应用
- 智能本地规则选择器，可分析项目结构并生成适合的规则

## 安装方式

### 通过.vsix文件安装（推荐）

1. 下载最新的 `.vsix` 文件
2. 在VSCode中，点击左侧扩展图标（或按`Ctrl+Shift+X`）
3. 点击扩展视图右上角的"..."，选择"从VSIX安装..."
4. 选择下载的 `.vsix` 文件

或者，您也可以使用命令行安装：
```bash
code --install-extension cursor-project-rules-0.1.0.vsix
```

### 从VSCode商店安装

1. 打开VSCode
2. 点击左侧扩展图标或按下 `Ctrl+Shift+X`
3. 在搜索框中输入 `Cursor Project Rules Generator`
4. 点击安装

## 项目结构

- `extension/` - VSCode扩展源代码
  - `src/` - TypeScript源文件（扩展主要逻辑）
  - `webview/` - 网页视图界面（前端界面）
- `scripts/` - Python转换脚本（规则处理和AI模型调用）
- `rules_data/` - 本地规则数据目录
  - `rules.db.json` - 规则数据库文件，包含所有可用规则

## 使用方法

1. 打开命令面板 (`Ctrl+Shift+P` 或 `F1`)
2. 输入 "Cursor" 查看可用命令：
   - `Cursor: 生成Project Rules` - 启动规则生成向导
   - `Cursor: 预览可用规则` - 查看可用的规则列表
   - `Cursor: 配置AI模型URL` - 设置自定义AI模型API地址
   - `Cursor: 配置AI模型API密钥` - 设置API访问密钥
   - `Cursor: 选择本地规则` - 从本地规则库中选择规则

3. 首次使用时，建议先配置AI模型信息（如果使用自定义模型）

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
  - 可以指定自定义模板目录，用于生成规则
  
- `cursor-rules.modelUrl`: AI模型API的URL地址
  - 默认值: 空
  - 例如: `https://api.openai.com/v1/chat/completions` 或其他模型服务的URL
  
- `cursor-rules.apiKey`: AI模型的API密钥
  - 默认值: 空
  - 您需要从模型提供商获取API密钥

- `cursor-rules.modelName`: 使用的AI模型名称
  - 默认值: `gpt-3.5-turbo`
  - 可根据实际使用的模型调整

## AI模型说明

本插件支持使用任何符合OpenAI API格式的模型服务，包括但不限于：

- OpenAI API (GPT-3.5, GPT-4等)
- DeepSeek
- Claude
- 本地部署的开源模型

模型需要支持生成规范格式的JSON输出。

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

## 规则数据库

本项目包含一个丰富的规则数据库（`rules_data/rules.db.json`），其中包含了各种编程语言、框架和工具的最佳实践规则。规则数据来源于：

1. cursor.directory网站 - 一个收集Cursor规则的社区网站
2. 开发者贡献的自定义规则
3. 从各种编程语言和框架的官方文档中提取的最佳实践

每条规则包含以下信息：
- `tags`: 标签列表，用于分类和筛选规则
- `title`: 规则标题
- `slug`: 规则的唯一标识符
- `libs`: 相关库或框架
- `content`: 规则内容，包含详细的编码指南和最佳实践
- `author`: 规则作者信息

您可以使用提供的脚本（`fetch_cursor_rules.js`）来更新规则数据库：

```bash
node fetch_cursor_rules.js
```

## 开发指南

### 编译和测试

```bash
# 编译TypeScript
npm run compile

# 持续监视并编译更改
npm run watch

# 运行扩展（在VSCode中）
按F5或从调试菜单启动
```

### 打包扩展

要将扩展打包为.vsix文件，请按照以下步骤操作：

```bash
# 安装vsce工具（如果尚未安装）
npm install -g @vscode/vsce

# 打包扩展
vsce package

# 这将在当前目录生成一个.vsix文件，例如：cursor-project-rules-0.1.0.vsix
```

您也可以使用以下命令指定版本号：

```bash
vsce package x.y.z  # 例如：vsce package 1.0.0
```

打包完成后，您可以通过以下方式安装扩展：

1. 在VSCode中，点击左侧扩展图标（或按`Ctrl+Shift+X`）
2. 点击扩展视图右上角的"..."，选择"从VSIX安装..."
3. 选择生成的.vsix文件

或者，使用命令行安装：

```bash
code --install-extension cursor-project-rules-x.y.z.vsix
```

## 故障排除

1. **无法调用AI模型**
   - 确认模型URL和API密钥配置正确
   - 检查网络连接是否正常
   - 查看日志输出，确认API请求细节

2. **规则生成失败**
   - 检查输出目录是否有写入权限
   - 确认AI模型返回内容符合预期格式
   - 查看日志中的错误信息进行调试 

## 项目反思与改进

在完成规则数据库的更新后，我们发现以下几点可以进一步改进：

1. **规则数据自动更新机制**：可以实现定期从cursor.directory网站自动获取最新规则的功能，确保规则库始终保持最新。

2. **规则质量评估**：添加规则质量评估机制，对规则进行评分，帮助用户选择高质量的规则。

3. **规则本地化**：支持规则的多语言版本，方便不同语言的用户使用。

4. **规则自定义与合并**：提供更灵活的规则自定义和合并功能，允许用户根据自己的需求组合不同的规则。

5. **规则版本控制**：实现规则的版本控制，方便用户在不同版本之间切换。

这些改进将在未来版本中逐步实现，以提供更好的用户体验。 

# Cursor Project Rules Generator

一个VSCode扩展，用于生成和管理Cursor项目规则。

## 功能

- **生成项目规则**: 从Cursor Directory中选择并生成项目规则
- **预览可用规则**: 查看所有可用的Cursor规则
- **搜索规则**: 支持按规则名称、类型和使用的库进行搜索
- **规则数据库更新**: 从在线源获取最新规则数据

## 使用方法

### 配置AI模型

首次使用前，需要配置AI模型信息：

1. 从命令面板选择 `Cursor: 配置AI模型URL`
2. 输入AI模型的API URL地址
3. 从命令面板选择 `Cursor: 配置API密钥`
4. 输入AI模型服务的API密钥

### 生成规则

1. 从命令面板选择 `Cursor: 生成项目规则`
2. 从列表中选择一个规则（支持搜索库名称）
3. 规则将被生成到项目的 `.cursor/rules` 目录中

### 更新规则数据库

1. 从命令面板选择 `Cursor: 更新规则数据库`
2. 扩展会自动从Cursor Directory获取最新规则数据
3. 更新完成后会显示新增的规则数量

## 扩展设置

此扩展提供以下设置：

* `cursor-rules.modelUrl`: AI模型API的URL
* `cursor-rules.apiKey`: AI模型服务的API密钥
* `cursor-rules.modelName`: 要使用的AI模型名称（默认为gpt-4）
* `cursor-rules.pythonPath`: Python解释器路径
* `cursor-rules.rulesSourceUrl`: 规则数据库更新源URL

## 最新功能

- **支持库搜索**: 规则选择器支持按库名称搜索
- **点击外部隐藏**: 选择规则时点击编辑器其他区域可隐藏列表
- **从网站获取规则**: 支持从Cursor Directory网站实时获取最新规则