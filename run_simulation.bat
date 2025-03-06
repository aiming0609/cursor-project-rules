@echo off
chcp 65001 > nul
echo 正在运行Cursor项目规则模拟器...
echo.

set USE_SAMPLE_RULES=1
echo 已设置使用样例规则模式
echo.

python scripts/simulate_extension.py

echo.
echo 模拟完成! 按任意键退出...
pause > nul 