@echo off
chcp 65001 > nul
echo ===== Cursor规则生成器 - AI模型配置助手 =====
echo.
echo 此工具将帮助您配置用于生成和定制规则的AI模型参数。
echo 配置完成后，您可以使用本地规则选择器生成定制化的规则。
echo.

set OPTION=%1

if "%OPTION%"=="--show" (
    python scripts/configure_model.py --show
    goto end
)

if "%OPTION%"=="--test" (
    python scripts/configure_model.py --test
    goto end
)

python scripts/configure_model.py

:end
echo.
echo 按任意键退出...
pause > nul 