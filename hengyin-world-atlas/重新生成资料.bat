@echo off
title 衡垠世界图集 - 重新生成资料
cd /d "%~dp0"
echo.
echo   ============================================================
echo     重新生成 AI 资料包与网页数据
echo   ============================================================
echo.
echo   依据 data/ 里的正式资料，重建索引、报告、ZIP 和网页数据岛。
echo   只有修改过 data/ 里的文件后才需要运行本脚本。
echo.

where python >nul 2>nul
if not errorlevel 1 goto HAVE_PYTHON
where py >nul 2>nul
if not errorlevel 1 goto HAVE_PY
echo   没有检测到 Python，无法重新生成。
echo   需要免费安装 Python 3；但只是浏览网站不需要 Python。
pause
exit /b

:HAVE_PYTHON
python tools\build_kb.py --sync
goto END

:HAVE_PY
py -3 tools\build_kb.py --sync
goto END

:END
echo.
echo   完成：新的「衡垠AI资料包.zip」已生成，网页数据岛已同步。
echo   按任意键关闭窗口。
pause >nul
