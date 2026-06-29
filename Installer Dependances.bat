@echo off
echo ============================================
echo   Installation des dependances
echo ============================================
echo.

where python >nul 2>nul
if %errorlevel% neq 0 (
    for %%P in (
        "%LOCALAPPDATA%\Programs\Python\Python314\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python313\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python311\python.exe"
        "%LOCALAPPDATA%\Programs\Python\Python310\python.exe"
    ) do (
        if exist %%P (
            set PYTHON_CMD=%%P
            goto :found
        )
    )
    echo [ERREUR] Python non trouve.
    echo Installez Python depuis https://python.org
    echo Cochez "Add Python to PATH" lors de l'installation.
    echo.
    pause
    exit /b 1
) else (
    set PYTHON_CMD=python
)

:found
echo Python trouve : %PYTHON_CMD%
echo.
echo Installation des packages...
echo.
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install pandas numpy pyarrow openpyxl flask
echo.
echo ============================================
echo   Verification
echo ============================================
echo.
%PYTHON_CMD% -c "import pandas; print(f'  pandas    {pandas.__version__}')"
%PYTHON_CMD% -c "import numpy; print(f'  numpy     {numpy.__version__}')"
%PYTHON_CMD% -c "import pyarrow; print(f'  pyarrow   {pyarrow.__version__}')"
%PYTHON_CMD% -c "import openpyxl; print(f'  openpyxl  {openpyxl.__version__}')"
%PYTHON_CMD% -c "import flask; print(f'  flask     {flask.__version__}')"
echo.
echo [OK] Toutes les dependances sont installees.
echo.
pause
