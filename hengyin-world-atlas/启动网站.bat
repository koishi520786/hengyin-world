@echo off
title 衡垠世界图集 - 本地网站
cd /d "%~dp0"
echo.
echo   ============================================================
echo     衡垠世界图集 · 本地网站
echo   ============================================================
echo.
echo   正在检查运行环境...
echo.

where python >nul 2>nul
if not errorlevel 1 goto HAVE_PYTHON
where py >nul 2>nul
if not errorlevel 1 goto HAVE_PY
goto NOPYTHON

:HAVE_PYTHON
echo   已找到 Python，正在启动本地服务（仅本机 127.0.0.1）。
echo   浏览器会自动打开；若没有打开，请手动访问窗口里显示的网址。
echo.
python tools\serve.py
goto END

:HAVE_PY
echo   已找到 Python 启动器，正在启动本地服务（仅本机 127.0.0.1）。
echo.
py -3 tools\serve.py
goto END

:NOPYTHON
echo   没有检测到 Python。
echo   别担心：本网站的数据已经内嵌在网页里，不装 Python 也能完整使用。
echo   现在将直接双击打开网页。
echo.
start "" "衡垠世界图集.html"
echo   已尝试用默认浏览器打开。以后直接双击「衡垠世界图集.html」即可。
echo.
pause
exit /b

:END
echo.
echo   服务已停止。按任意键关闭窗口。
pause >nul
