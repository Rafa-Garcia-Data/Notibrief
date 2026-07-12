@echo off
title Notibrief
echo ========================================
echo   NOTIBRIEF - Iniciando servidor...
echo ========================================
echo.

docker compose up -d --build
if errorlevel 1 (
    echo.
    echo ERROR: No se pudo iniciar Docker. Asegurate de que Docker Desktop esta ejecutandose.
    pause
    exit /b 1
)

echo Esperando a que el servidor este listo...
:wait
timeout /t 2 /nobreak >nul
curl -s http://localhost:8787/api/status >nul 2>&1
if errorlevel 1 goto wait

echo.
echo Servidor listo. Abriendo navegador...
start http://localhost:8787

echo.
echo ========================================
echo   NOTIBRIEF activo en http://localhost:8787
echo   Para parar: usa el boton en la web o stop.bat
echo ========================================
echo.
pause
