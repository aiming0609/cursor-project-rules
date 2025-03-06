@echo off
echo ===== Cursor Project Rules Generator 修复工具 =====
echo.
echo 正在设置控制台编码...
chcp 65001 > nul

echo.
echo 1. 正在修复编码问题...
python scripts/fix_encoding.py
echo.

echo 2. 编译TypeScript代码...
call npm run compile
echo.

echo 3. 运行模拟脚本（使用样例规则）...
set IGNORE_NETWORK_ERRORS=1
python scripts/simulate_extension.py
echo.

echo ===== 完成 =====
echo.
echo 如果您看到"示例规则生成成功"的消息，说明扩展已经可以使用样例规则正常工作。
echo 您可以在VSCode中运行扩展，或者继续使用模拟脚本测试功能。
echo.
echo 生成的规则文件位于：.cursor/rules/ 目录
echo.
pause 