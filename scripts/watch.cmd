@echo off
cd /d "
C:\Users\wajeehan computer\Documents\Default Project\arl-sbu-recovery-dashboard
"
set PYTHONIOENCODING=utf-8
"
C:\Users\wajeehan computer\AppData\Local\Programs\Python\Python313\python.exe
" "scripts\auto_refresh.py" >> "logs\auto_refresh.log" 2>&1
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\push.ps1" >> "logs\auto_refresh.log" 2>&1
