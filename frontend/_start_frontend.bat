@echo off
cd /d "%~dp0"
call npm run export || goto :hiba
call npm run patch-dist || goto :hiba
echo.
echo Megnyithatod: http://localhost:8081
call npx --yes serve -s dist -l 8081
goto :vege
:hiba
echo.
echo A build elhasalt. A fenti hibauzenet mondja meg, hol.
pause
:vege
