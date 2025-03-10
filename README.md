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

## 故障排除

1. **无法调用AI模型**
   - 确认模型URL和API密钥配置正确
   - 检查网络连接是否正常
   - 查看日志输出，确认API请求细节

2. **规则生成失败**
   - 检查输出目录是否有写入权限
   - 确认AI模型返回内容符合预期格式
   - 查看日志中的错误信息进行调试 