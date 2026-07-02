@echo off
rem ZTT screener scan — wired to Windows Task Scheduler every 10 minutes
rem (task name: ZerosRequiem\ZTT Screener, registered 2026-07-02).
rem Alert-only: reads OANDA data, writes logs\ztt_screener\ — places NO orders.
cd /d "C:\Users\jamie\OneDrive\Documents\Jamie VS Code\Git\Zeros Requiem"
venv\Scripts\python.exe -m src.live.ztt_screener >> logs\ztt_screener\scheduler_run.log 2>&1
