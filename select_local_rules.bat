@echo off
chcp 65001 > nul
echo ===== Cursor 本地规则选择工具 =====
echo.
echo 此工具将从本地JSON文件加载规则，并允许您选择要应用的规则。
echo 选中的规则将使用AI模型进行分析和定制，然后转换为Cursor项目规则格式。
echo 规则文件将保存在.cursor/rules目录中。
echo.
echo 注意: 此工具需要AI模型配置，首次运行时可能会提示您输入模型URL和API密钥信息。
echo 您可以通过环境变量 CURSOR_RULES_MODEL_URL、CURSOR_RULES_API_KEY 和 CURSOR_RULES_MODEL_NAME 预先配置。
echo.

set WORKSPACE_PATH=%CD%
set RULES_JSON=rules_data/rules.db.json

if not exist "%RULES_JSON%" (
    echo 错误: 找不到规则数据文件 %RULES_JSON%
    echo 请确保您已下载规则数据文件并放置在正确的位置。
    echo.
    goto end
)

echo 正在启动规则选择器...
python scripts/local_rules_selector.py --workspace "%WORKSPACE_PATH%" --rules-json "%RULES_JSON%"

:end
echo.
echo 按任意键退出...
pause > nul 