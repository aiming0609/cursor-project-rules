@echo off
chcp 65001 > nul
echo ===== Cursor Directory 网站测试工具 =====
echo.

:menu
echo 请选择要运行的测试:
echo 1. 基本网站测试 (自动模式)
echo 2. 交互式网站测试 (可探索网页结构和测试选择器)
echo 3. 离线模式测试 (使用已保存的HTML文件)
echo 4. 退出
echo.

set /p choice=请输入选项 (1-4): 

if "%choice%"=="1" (
    echo.
    echo 正在运行基本网站测试...
    python scripts/test_fetch_rules.py
    goto end
)

if "%choice%"=="2" (
    echo.
    echo 正在启动交互式网站测试...
    python scripts/test_fetch_interactive.py --interactive
    goto end
)

if "%choice%"=="3" (
    set /p html_file=请输入HTML文件路径 (默认: cursor_directory_latest.html): 
    
    if "%html_file%"=="" (
        set html_file=cursor_directory_latest.html
    )
    
    if not exist "%html_file%" (
        echo 错误: 文件 %html_file% 不存在!
        echo.
        goto menu
    )
    
    echo.
    echo 正在使用离线文件 %html_file% 进行测试...
    python scripts/test_fetch_interactive.py --offline "%html_file%" --interactive
    goto end
)

if "%choice%"=="4" (
    echo 正在退出...
    goto exit
)

echo.
echo 无效的选项，请重新选择。
echo.
goto menu

:end
echo.
echo 测试完成!
echo.
echo 如果要保存最新的网站HTML内容，可以在脚本目录中找到 cursor_directory_latest.html 文件。
echo 如果要进行更深入的测试，可以选择选项2进入交互式模式。
echo.
echo 按任意键返回主菜单...
pause > nul
goto menu

:exit 