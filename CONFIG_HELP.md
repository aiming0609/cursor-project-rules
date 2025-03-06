# 配置帮助指南

## 问题解决

您遇到的问题：
1. 即使已经配置了模型名称和URL，扩展仍然一直弹出配置提示
2. 找不到API密钥的配置项

我们已经修复了这些问题，现在您可以通过以下方法解决：

## 解决方法1：使用命令面板配置

1. 打开VSCode命令面板（按下`Ctrl+Shift+P`或`Cmd+Shift+P`）
2. 输入并选择"Cursor: 配置AI模型URL"来配置模型URL
3. 再次打开命令面板，输入并选择"Cursor: 配置AI模型API密钥"来配置API密钥

## 解决方法2：直接在设置中配置

1. 打开VSCode设置（按下`Ctrl+,`或`Cmd+,`）
2. 在搜索框中输入"cursor-rules"
3. 您将看到所有相关设置，包括：
   - `cursor-rules.modelUrl`：AI模型API的URL地址
   - `cursor-rules.apiKey`：AI模型的API密钥
   - `cursor-rules.modelName`：使用的AI模型名称

## 解决方法3：使用辅助脚本配置

我们创建了一个辅助脚本来帮助您配置API密钥：

```bash
python scripts/configure_api_key.py
```

运行此脚本，按照提示输入您的API密钥，它将自动更新VSCode设置。

## 关于重复提示的问题

我们已经修改了代码，现在扩展只会在首次运行时检查配置，之后不会再频繁提示。如果您仍然收到提示，可以：

1. 确保您已经正确配置了模型URL
2. 选择提示中的"不再提醒"选项
3. 重新启动VSCode

## 配置示例

### 模型URL示例
```
https://api.openai.com/v1/chat/completions
```

### API密钥示例
```
sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

### 模型名称示例
```
gpt-3.5-turbo
```

## 其他注意事项

- 配置完成后，您需要重新启动VSCode或重新加载窗口才能使更改生效
- 如果您使用的是本地模型，请确保模型服务器已启动
- 如果您仍然遇到问题，可以尝试运行`scripts/simulate_extension.py`脚本来测试核心功能 