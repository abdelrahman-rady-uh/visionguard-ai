@echo off
REM =====================================================
REM VisionGuard AI - One-click rebuild with embedded figures
REM Just double-click this file. No editing required.
REM =====================================================

setlocal
cd /d "%~dp0"

echo.
echo ==================================================
echo   VisionGuard AI - Final Report Rebuilder
echo ==================================================
echo.

REM Try common Python launchers (py first, then python)
set "PYCMD="
where py >nul 2>nul && set "PYCMD=py -3"
if "%PYCMD%"=="" where python >nul 2>nul && set "PYCMD=python"
if "%PYCMD%"=="" (
    echo [ERROR] Python is not on PATH.
    echo.
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo and tick "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

echo [1/3] Installing required Python libraries (one-time, quiet)...
%PYCMD% -m pip install --quiet --upgrade python-docx matplotlib numpy scipy Pillow
if errorlevel 1 (
    echo [WARN] pip had issues. Retrying with --user...
    %PYCMD% -m pip install --quiet --user --upgrade python-docx matplotlib numpy scipy Pillow
)

echo.
echo [2/3] Generating 33 figures (charts, diagrams, mockups)...
%PYCMD% "%~dp0visionguard_rebuild_part_a_figures.py"
if errorlevel 1 (
    echo [ERROR] Figure generation failed. See message above.
    pause
    exit /b 1
)

echo.
echo [3/3] Building Word document with figures embedded...
%PYCMD% "%~dp0visionguard_rebuild_part_b_document.py"
if errorlevel 1 (
    echo [ERROR] Document build failed. See message above.
    pause
    exit /b 1
)

echo.
echo ==================================================
echo   DONE!
echo   File: VisionGuard_AI_Final_Report.docx
echo   Location: %~dp0
echo ==================================================
echo.
echo Opening the document...
start "" "%~dp0VisionGuard_AI_Final_Report.docx"

pause
endlocal
