@echo off
echo ============================================
echo   Serveur - Extraction de Donnees
echo ============================================
echo.

:: Chercher Python dans le PATH
where python >nul 2>nul
if %errorlevel% equ 0 (
    set PYTHON_CMD=python
    goto :found
)

:: Chercher dans les emplacements courants
for %%P in (
    "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
    "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    "C:\Python314\python.exe"
    "C:\Python313\python.exe"
    "C:\Python312\python.exe"
) do (
    if exist %%P (
        set PYTHON_CMD=%%P
        goto :found
    )
)

echo [ERREUR] Python non trouve.
echo Installez Python depuis https://python.org
echo Cochez "Add Python to PATH" lors de l'installation.
pause
exit /b 1

:found
echo Python trouve : %PYTHON_CMD%
echo.
echo Verification des packages...
%PYTHON_CMD% -c "import pandas, flask, pyarrow" 2>nul
if %errorlevel% neq 0 (
    echo Installation des packages necessaires...
    %PYTHON_CMD% -m pip install pandas numpy pyarrow openpyxl flask
    echo.
)

echo Le serveur demarre... Ne fermez pas cette fenetre.
echo Pour arreter : CTRL+C ou fermez cette fenetre.
echo ============================================
echo.
%PYTHON_CMD% "%~dp0scripts\api_extraction.py"
pause
