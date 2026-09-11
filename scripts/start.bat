@echo off
chcp 65001 >nul
echo ========================================
echo   NovaTech 智能客服 — 一键启动脚本
echo ========================================
echo.

echo [1/3] 启动 Mock API...
docker-compose up -d mock_api
if errorlevel 1 (
    echo [错误] Mock API 启动失败，请检查 Docker 是否运行
    pause
    exit /b 1
)

echo.
echo [2/3] 等待 API 就绪...
timeout /t 5 /nobreak >nul

echo.
echo [3/3] 验证 API 连通性...
curl -s http://localhost:3000/api/logistics?order_id=NV202609080001
echo.
echo.

echo ========================================
echo   启动完成！
echo   Mock API: http://localhost:3000
echo   Dify:     http://localhost
echo ========================================
echo.
pause
