# 调试与测试说明

## 运行VSCode扩展

现在TypeScript代码已经成功编译，可以按照以下步骤在VSCode中运行和测试该扩展：

1. 在VSCode中打开此项目文件夹
2. 按下`F5`键或点击侧边栏的"运行和调试"按钮，然后选择"运行扩展"
3. 这将打开一个新的VSCode窗口（扩展开发主机），其中已加载了我们的扩展

## 测试步骤

在扩展开发主机窗口中：

1. **测试配置模型设置**:
   - 打开命令面板（按下`Ctrl+Shift+P`或`Cmd+Shift+P`）
   - 输入并选择"Cursor: 配置AI模型设置"
   - 在设置页面中，设置以下选项：
     - `cursor-rules.modelUrl`: 输入你的AI模型API URL（例如：`https://api.openai.com/v1/chat/completions`）
     - `cursor-rules.apiKey`: 输入你的API密钥
     - `cursor-rules.modelName`: 保留默认值或更改为你要使用的模型名称

2. **测试预览可用规则**:
   - 打开命令面板
   - 输入并选择"Cursor: 预览可用规则"
   - 将显示一个WebView页面，尝试从Cursor Directory加载规则

3. **测试生成规则**:
   - 打开命令面板
   - 输入并选择"Cursor: 生成Project Rules"
   - 脚本将尝试获取规则并转换为Cursor项目规则格式
   - 规则文件将被保存在项目的`.cursor/rules/`目录中

## 验证结果

执行上述操作后，请检查：

1. 扩展是否成功加载并显示配置提示
2. 命令面板是否显示我们的三个命令
3. 模型配置页面是否正确显示
4. 预览规则页面是否成功加载
5. 生成规则命令执行后，是否成功创建了`.cursor/rules/`目录和规则文件
6. 查看输出面板中的日志信息（可以通过点击底部的"输出"标签页查看）

## 注意事项

- 第一次运行时，可能会显示模型配置提示
- 由于没有实际的有效API URL和密钥，预期规则生成步骤会失败
- 你可以使用`scripts/test_binary_write.py`脚本来测试二进制写入功能：
  ```
  python scripts/test_binary_write.py
  ```
  这将创建一个测试规则文件在`.cursor/rules/`目录中 