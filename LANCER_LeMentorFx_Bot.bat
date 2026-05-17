@echo off
title LeMentorFx Bot V5 - @lementorfx
color 0A
echo.
echo  ====================================
echo   LEMENTORFX BOT V5 - Demarrage...
echo   Ne fermez pas cette fenetre !
echo  ====================================
echo.
cd /d "%USERPROFILE%\Desktop\BOTS"
pip install python-telegram-bot==20.3 -q
python lementorfx_bot.py
echo.
echo  Bot arrete. Appuyez sur une touche pour relancer.
pause
python lementorfx_bot.py
