@echo off
echo ============================================
echo   Serveur Ooredoo - Extraction de Donnees
echo ============================================
echo.
echo Le serveur demarre... Ne fermez pas cette fenetre.
echo Le navigateur va s'ouvrir automatiquement.
echo.
echo Pour arreter le serveur : CTRL+C ou fermez cette fenetre.
echo ============================================
echo.
python "%~dp0scripts\api_extraction.py"
pause
