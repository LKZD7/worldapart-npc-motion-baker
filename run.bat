@echo off
chcp 65001 >nul
title 不问凡尘·视频分段生成工具

echo ======================================
echo       参数输入
echo ======================================
set /p space_id=请输入5位SpaceID(例:15011): 
set /p npc_id=请输入6位NpcID(例:150101): 

if "%space_id%"=="" (
    echo 错误：SpaceID不能为空！
    pause
    exit /b 1
)
if "%npc_id%"=="" (
    echo 错误：NpcID不能为空！
    pause
    exit /b 1
)

echo.
echo SpaceID=%space_id%
echo NpcID=%npc_id%
echo --------------------------------------

.\python-3.15.2-embed-win32\python proc.py %space_id% %npc_id%

echo.
echo 删除临时文件夹tmp_frames
rd /s /q tmp_frames
echo ======================================
echo 脚本执行完成
echo ======================================
pause
