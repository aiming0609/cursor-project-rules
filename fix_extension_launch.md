# 修复VSCode扩展启动问题

您在尝试运行VSCode扩展时遇到了错误："没有用于查看 Markdown 的扩展"。这是因为VSCode试图打开一个Markdown文件但找不到相应的渲染器。

## 解决方案选项

### 选项1：安装Markdown扩展（推荐）

1. 在弹出的对话框中点击"查找 Markdown 扩展"按钮
2. 安装官方的Markdown扩展（通常是第一个选项）
3. 安装后重新尝试运行扩展

这是最简单的解决方法，安装Markdown扩展不会影响我们的扩展功能。

### 选项2：修改启动配置

如果您不想安装额外的扩展，请手动修改`.vscode/launch.json`文件：

1. 打开项目根目录下的`.vscode`文件夹
2. 编辑`launch.json`文件（如果不存在则创建）
3. 将以下内容粘贴到文件中：

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "运行扩展",
      "type": "extensionHost",
      "request": "launch",
      "args": [
        "--extensionDevelopmentPath=${workspaceFolder}",
        "--disable-extensions"
      ],
      "outFiles": [
        "${workspaceFolder}/extension/out/**/*.js"
      ],
      "preLaunchTask": "${defaultBuildTask}"
    }
  ]
}
```

4. 保存文件并重新尝试运行扩展

这个配置添加了`--disable-extensions`参数，它会在启动扩展开发主机时禁用所有其他扩展，从而避免Markdown扩展缺失的问题。

### 选项3：使用模拟脚本测试扩展功能

如果您仍然无法启动扩展，可以使用我们之前创建的模拟脚本来测试核心功能：

```bash
python scripts/simulate_extension.py
```

这个脚本模拟了扩展的核心功能，包括规则获取和二进制写入，可以帮助您验证最关键的功能是否正常工作。

## 其他注意事项

- 确保TypeScript已经成功编译（`npm run compile`）
- 检查Python依赖是否已正确安装（`pip install -r scripts/requirements.txt`）
- 在使用模拟脚本测试后，可以检查`.cursor/rules`目录中的内容，验证二进制写入功能是否正常 